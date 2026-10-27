fn is_safe(available: [i32; 3], max: [[i32; 3]; 3], alloc: [[i32; 3]; 3]) -> bool {
    let mut need = [[0; 3]; 3];
    for i in 0..3 {
        for j in 0..3 { need[i][j] = max[i][j] - alloc[i][j]; }
    }
    let mut work = available;
    let mut finished = [false; 3];
    for _ in 0..3 {
        for i in 0..3 {
            let fits = (0..3).all(|j| need[i][j] <= work[j]);
            if !finished[i] && fits {
                for j in 0..3 { work[j] += alloc[i][j]; }
                finished[i] = true;
            }
        }
    }
    finished.iter().all(|&f| f)
}

fn main() {
    let available = [3, 3, 2];
    let max = [[4, 3, 2], [3, 2, 2], [9,0,2]];
    let alloc = [[1, 1, 0], [2, 0, 1], [1, 1, 1]];
    println!("safe state? {}", is_safe(available, max, alloc));
}
