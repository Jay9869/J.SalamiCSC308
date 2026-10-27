use std::sync::Mutex;
use std::thread;
//use std::time::Duration;

// the fix is to remove the sleep as it wastes cpu time and ensure both threads have the same execution order
// so that they race but not deadlock. If thread1 A gets there first, thread2 also tries to access that same A
// but it wont deadlock, it will wait till it finishes
fn main() {
    let lock_a = Mutex::new(0);
    let lock_b = Mutex::new(0);
    thread::scope(|s| {
        s.spawn(|| {
            let _a = lock_a.lock().unwrap();
            println!("thread 1: got lock A, waiting for B");
//            (Duration::from_millis(100));
            let _b = lock_b.lock().unwrap();
            println!("thread 1: got both locks");
        });
        s.spawn(|| {
            let _b = lock_b.lock().unwrap();
            println!("thread 2: got lock B, waiting for A");
  //          (Duration::from_millis(100));
            let _a = lock_a.lock().unwrap();
            println!("thread 2: got both locks");
        });
    });
    println!("both threads finished");
}

