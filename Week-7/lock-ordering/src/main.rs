use std::sync::{Mutex, MutexGuard};
use std::thread;
// use std::time::Duration;

fn lock_in_order<'a>(a: &'a Mutex<i32>, b: &'a Mutex<i32>) -> (MutexGuard<'a, i32>, MutexGuard<'a, i32>) {
    let a_addr = a as *const Mutex<i32> as usize;
    let b_addr = b as *const Mutex<i32> as usize;
    if a_addr < b_addr {
        (a.lock().unwrap(), b.lock().unwrap())
    } else {
        (b.lock().unwrap(), a.lock().unwrap())
    }
}

fn main() {
    let lock_a = Mutex::new(0);
    let lock_b = Mutex::new(0);
    let lock_c = Mutex::new(0);

    thread::scope(|s| {
        s.spawn(|| {
            // WITHOUT HELPER FUNCTION

            // let _a = lock_a.lock().unwrap();
            // println!("thread 1: got lock A, waiting for B");
            // // thread::sleep(Duration::from_millis(100));
            // let _b = lock_b.lock().unwrap();
            // // lock_in_order(lock_a, lock_b);
            // println!("thread 1: got lock B, waiting for C");
            // let _c = lock_c.lock().unwrap();
            // println!("thread 1: got all locks");

            let _a = lock_a.lock().unwrap();
            println!("thread 1: got lock A, waiting for B");
            let _b = lock_b.lock().unwrap();
            println!("thread 1: got lock B, waiting for C");
            let _c = lock_c.lock().unwrap();
            println!("thread 1: got all locks");
        });
        s.spawn(|| {
            // WITHOUT HELPER FUNCTION

            // let _a = lock_a.lock().unwrap();
            // println!("thread 2: got lock A, waiting for B");
            // // thread::sleep(Duration::from_millis(100));
            // let _b = lock_b.lock().unwrap();
            // // lock_in_order(lock_a, lock_b);
            // println!("thread 2: got lock B, waiting for C");
            // let _c = lock_c.lock().unwrap();
            // println!("thread 2: got all locks");

            let _a = lock_a.lock().unwrap();
            println!("thread 2: got lock A, waiting for B");
            let _b = lock_b.lock().unwrap();
            println!("thread 2: got lock B, waiting for C");
            let _c = lock_c.lock().unwrap();
            println!("thread 2: got all locks");
        });
    });
    println!("both threads finished");
}
