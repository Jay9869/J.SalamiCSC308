/* What this code does is that first we spawn a thread for the particular loop
   The closure allows the thread to run a loop and .join() line executes it
*/

use std::thread;
fn main() 
{
    let handle = thread::spawn(|| {
        for i in 1..5 {
            println!("hi number {} from the first thread!", i);
        } 
    }); 
    let handle2 = thread::spawn(|| {
        for i in 1..5 {
            println!("hi number {} from the second thread!", i);
        } 
    }); 
    let handle3 = thread::spawn(|| {
        for i in 1..5 {
            println!("hi number {} from the third thread!", i);
        } 
    }); 
    handle.join().unwrap();
    handle2.join().unwrap();
    handle3.join().unwrap();
    // .join() is used to prevent your thread from outliving your program
    // unwrap() outputs a Result<T,E>. Okay = T, Error = T
    println!("done in main");
}