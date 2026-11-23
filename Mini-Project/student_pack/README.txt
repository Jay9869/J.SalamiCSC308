CSC 308 mini project: student pack
==================================

What is in here
  selfcheck.py   builds your project and runs the PUBLIC tests against it
  tests/         the public test cases for each track (NAME.in is the input, NAME.out is the expected output)

How to use it (Linux or WSL terminal; you need Rust and Python 3)
  python3 selfcheck.py --project path/to/your/project --track memory --tests tests

  --track is memory, scheduler or shell (see the brief for which one is yours).
  For every test that fails it prints the input, the expected output and your output.

Notes
  * The hidden tests used for marking follow the same rules but use different inputs and edge cases.
  * Outputs are compared after ignoring extra spaces at the ends and between words.
  * Your program is stopped after 5 seconds per test.
  * The shell track tests use ordinary Linux tools (echo, cat, sort, wc, tr, mkdir), so run them in WSL/Linux.

Submitting
  * Save your zip file with your matric number ONLY, for example 24120111001.zip (nothing else in the name).
  * Inside: Cargo.toml, the src folder and README.md. Leave out the target folder.
  * You have one week. Submit before next week's class; you will defend your code in that class.
