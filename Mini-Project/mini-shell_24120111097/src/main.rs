use std::io::{self, BufRead};
use std::process::Command;

fn main() {
    let stdin = io::stdin();

    // Read the input one line at a time. Each line is one command.
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break, // could not read: stop the shell
        };

        // Split the line into words (splits on any amount of spaces).
        let words: Vec<&str> = line.split_whitespace().collect();

        // STEP 2: blank line -> ignore it and go to the next line
        if words.is_empty() {
            continue;
        }

        // STEP 3: "exit" -> stop the shell
        if words[0] == "exit" {
            break;
        }

        // STEP 4 (later): "cd" must be handled here, BEFORE running programs.

        // STEP 1: run an ordinary program (this is all you need for echo/cat/etc.)
        run_simple(&words);
    }
}

// Runs one program with its arguments and waits for it to finish.
fn run_simple(words: &[&str]) {
    let program = words[0];
    let args = &words[1..];

    match Command::new(program).args(args).spawn() {
        Ok(mut child) => {
            let _ = child.wait(); // wait for the program to finish
        }
        Err(e) => {
            // Errors go to STANDARD ERROR (eprintln!), never to stdout.
            eprintln!("{}: {}", program, e);
        }
    }
}