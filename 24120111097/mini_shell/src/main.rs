use std::env;
use std::fs::File;
use std::io::{self, BufRead};
use std::process::{Command, Stdio};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();

    while let Some(Ok(line)) = lines.next() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        if trimmed.split_whitespace().next() == Some("exit") {
            break;
        }

        if trimmed.contains('|') {
            let parts: Vec<&str> = trimmed.split('|').collect();
            if parts.len() == 2 {
                execute_pipeline(parts[0], parts[1]);
            } else {
                eprintln!("only one pipe is supported");
            }
            continue;
        }

        execute_single_command(trimmed);
    }
}

fn parse_redirection(input: &str) -> (&str, Option<&str>) {
    if let Some(idx) = input.find('>') {
        let cmd_part = input[..idx].trim();
        let file_part = input[idx + 1..].trim();
        (cmd_part, Some(file_part))
    } else {
        (input, None)
    }
}

fn parse_args(input: &str) -> Vec<&str> {
    input.split_whitespace().collect()
}

fn execute_single_command(cmd_str: &str) {
    let (clean_cmd, stdout_file) = parse_redirection(cmd_str);
    let args = parse_args(clean_cmd);

    if args.is_empty() {
        return;
    }

    let program = args[0];

    if program == "cd" {
        if args.len() < 2 {
            eprintln!("cd: missing argument");
        } else {
            let dir = args[1];
            if let Err(e) = env::set_current_dir(dir) {
                eprintln!("cd: {}", e);
            }
        }
        return;
    }

    let mut command = Command::new(program);
    command.args(&args[1..]);

    if let Some(file_path) = stdout_file {
        match File::create(file_path) {
            Ok(file) => {
                command.stdout(Stdio::from(file));
            }
            Err(e) => {
                eprintln!("Failed to create output file: {}", e);
                return;
            }
        }
    }

    match command.status() {
        Ok(_) => {}
        Err(_) => {
            eprintln!("Command not found: {}", program);
        }
    }
}

fn execute_pipeline(cmd1_str: &str, cmd2_str: &str) {
    let args1 = parse_args(cmd1_str);
    let (clean_cmd2, stdout_file) = parse_redirection(cmd2_str);
    let args2 = parse_args(clean_cmd2);

    if args1.is_empty() || args2.is_empty() {
        return;
    }

    let mut child1_builder = Command::new(args1[0]);
    child1_builder.args(&args1[1..]).stdout(Stdio::piped());

    let mut child1 = match child1_builder.spawn() {
        Ok(child) => child,
        Err(_) => {
            eprintln!("Command not found: {}", args1[0]);
            return;
        }
    };

    let pipe_reader = child1.stdout.take().unwrap();

    let mut child2_builder = Command::new(args2[0]);
    child2_builder
        .args(&args2[1..])
        .stdin(Stdio::from(pipe_reader));

    if let Some(file_path) = stdout_file {
        match File::create(file_path) {
            Ok(file) => {
                child2_builder.stdout(Stdio::from(file));
            }
            Err(e) => {
                eprintln!("Failed to create output file: {}", e);
                return;
            }
        }
    }

    let mut child2 = match child2_builder.spawn() {
        Ok(child) => child,
        Err(_) => {
            eprintln!("Command not found: {}", args2[0]);
            let _ = child1.kill();
            return;
        }
    };

    drop(child2_builder);

    let _ = child1.wait();
    let _ = child2.wait();
}