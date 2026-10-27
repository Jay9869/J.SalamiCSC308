use std::sync::Mutex;

fn main() {
    let counter = Mutex::new(0);

    {
        let mut num = counter.lock().unwrap();
        *num += 1;
        println!("counter = {}", *counter.lock().unwrap()); // causes an error (deadlock)
        // we can only lock again in another scope

    } // lock released here

    println!("counter = {}", *counter.lock().unwrap());
    println!("counter = {}", *counter.lock().unwrap());

}