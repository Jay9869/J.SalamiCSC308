#!/usr/bin/env python3
"""
CSC 308 mini project grader.

Instructor use (whole class):
    python3 grade.py --zips submissions/ --tests tests/ --out results/

  * Each zip is named <matric>.zip (for example 24120111001.zip).  The LAST DIGIT of the matric number
    picks the track:  0,1,9 = memory   2,4,6,8 = scheduler   3,5,7 = shell.
  * Writes results/results.csv (one row per student) and results/<matric>.txt (feedback with the
    failing tests).  Marks out of 7 are computed here:  build 1 + public 4 + hidden 2.
    README (1) and the defence in class (2) are marked by hand.

Student use (self-check of one project folder against the public tests only):
    python3 grade.py --project my_project_folder --track memory --tests tests/

Run the instructor mode inside a virtual machine or container: it builds and runs students' code.
"""
import argparse, csv, json, os, re, shutil, subprocess, sys, tempfile, zipfile, time

TRACKS = {'memory': 'memory', 'scheduler': 'scheduler', 'shell': 'shell'}
BUILD_TIMEOUT = 180
RUN_TIMEOUT = 5
MAX_TIMEOUTS = 2   # after this many timeouts in a row the remaining tests are marked failed without running

def track_of(matric):
    m = re.search(r'(\d)\D*$', matric)
    if not m:
        return None
    d = int(m.group(1))
    return 'memory' if d in (0, 1, 9) else 'scheduler' if d in (2, 4, 6, 8) else 'shell'

def find_project(root):
    """Return the folder that holds Cargo.toml (root itself or one or two levels down)."""
    for depth in range(3):
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ('target', '__MACOSX', '.git')]
            rel = os.path.relpath(base, root)
            d = 0 if rel == '.' else rel.count(os.sep) + 1
            if d == depth and 'Cargo.toml' in files:
                return base
    return None

def build(project):
    try:
        p = subprocess.run(['cargo', 'build', '--release', '--offline', '-q'], cwd=project,
                           capture_output=True, text=True, timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, 'build timed out'
    if p.returncode != 0:
        return None, 'build failed:\n' + p.stderr[-1500:]
    try:
        meta = subprocess.run(['cargo', 'metadata', '--no-deps', '--format-version', '1', '--offline'],
                              cwd=project, capture_output=True, text=True, timeout=60)
        j = json.loads(meta.stdout)
        tdir = j['target_directory']
        bins = [t['name'] for pk in j['packages'] for t in pk['targets'] if 'bin' in t['kind']]
    except Exception as e:
        return None, f'could not locate the binary: {e}'
    if not bins:
        return None, 'no binary target (is there a src/main.rs?)'
    exe = os.path.join(tdir, 'release', bins[0])
    if os.name == 'nt': exe += '.exe'
    return (exe, None) if os.path.exists(exe) else (None, 'binary not found after build')

def norm_lines(text):
    return [' '.join(l.split()) for l in text.strip().splitlines()]

def close_enough(got, exp):
    g, e = norm_lines(got), norm_lines(exp)
    if len(g) != len(e):
        return False
    for a, b in zip(g, e):
        if a == b:
            continue
        # numeric tolerance on the averages line only
        if a.startswith('avg_') and b.startswith('avg_'):
            ra = dict(x.split('=') for x in a.split()); rb = dict(x.split('=') for x in b.split())
            try:
                if ra.keys() == rb.keys() and all(abs(float(ra[k]) - float(rb[k])) <= 0.011 for k in ra):
                    continue
            except ValueError:
                pass
        return False
    return True

def run_program(exe, inp, work, env):
    """Run exe with inp on stdin in its own process group so that a hung shell and its children can be killed."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         cwd=work, env=env, start_new_session=(os.name != 'nt'))
    try:
        out, _ = p.communicate(inp, timeout=RUN_TIMEOUT)
        return out, p.returncode, False
    except subprocess.TimeoutExpired:
        try:
            if os.name != 'nt':
                import signal
                os.killpg(p.pid, signal.SIGKILL)
            else:
                p.kill()
        except Exception:
            pass
        try:
            p.communicate(timeout=2)
        except Exception:
            pass
        return '', None, True

def run_tests(exe, track, tests_dir, kinds):
    results = {k: [] for k in kinds}
    timeouts_in_a_row = 0
    for kind in kinds:
        d = os.path.join(tests_dir, track, kind)
        if not os.path.isdir(d):
            continue
        for f in sorted(x for x in os.listdir(d) if x.endswith('.in')):
            name = f[:-3]
            inp = open(os.path.join(d, f)).read()
            exp = open(os.path.join(d, name + '.out')).read()
            if timeouts_in_a_row >= MAX_TIMEOUTS:
                results[kind].append((name, False, inp, exp, '', 'skipped after repeated timeouts'))
                continue
            work = tempfile.mkdtemp(prefix='mp_')
            env = dict(os.environ, LC_ALL='C')
            try:
                got, rc, timed_out = run_program(exe, inp, work, env)
                if timed_out:
                    ok, note = False, 'timed out'; timeouts_in_a_row += 1
                else:
                    ok = close_enough(got, exp); note = ''; timeouts_in_a_row = 0
                    if not ok and rc not in (0, None) and track != 'shell':
                        note = f'exit code {rc} (crash?)'
            except Exception as e:
                ok, got, note = False, '', f'could not run: {e}'
            finally:
                shutil.rmtree(work, ignore_errors=True)
            results[kind].append((name, ok, inp, exp, got, note))
    return results

def feedback(results, show_hidden_detail):
    out = []
    for kind, lst in results.items():
        passed = sum(1 for r in lst if r[1])
        out.append(f'{kind}: {passed}/{len(lst)} passed')
        for name, ok, inp, exp, got, note in lst:
            if ok:
                out.append(f'  PASS {name}')
                continue
            out.append(f'  FAIL {name} {note}')
            if kind == 'public' or show_hidden_detail:
                out.append('    input:\n' + ''.join('      ' + l + '\n' for l in inp.splitlines()))
                out.append('    expected:\n' + ''.join('      ' + l + '\n' for l in exp.splitlines()))
                out.append('    got:\n' + ''.join('      ' + l + '\n' for l in got.splitlines()[:15]))
    return '\n'.join(out)

def readme_info(project):
    for n in ('README.md', 'readme.md', 'README.txt', 'README', 'Readme.md'):
        p = os.path.join(project, n)
        if os.path.exists(p):
            try:
                return True, len(open(p, errors='ignore').read().split())
            except Exception:
                return True, 0
    return False, 0

def grade_one(project, track, tests_dir, kinds):
    exe, err = build(project)
    if exe is None:
        return dict(built=0, results={k: [] for k in kinds}, error=err)
    return dict(built=1, results=run_tests(exe, track, tests_dir, kinds), error=None)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--zips'); ap.add_argument('--out', default='results')
    ap.add_argument('--project'); ap.add_argument('--track', choices=list(TRACKS))
    ap.add_argument('--tests', default='tests')
    ap.add_argument('--hidden-detail', action='store_true', help='include hidden test inputs in the feedback files')
    a = ap.parse_args()

    if a.project:   # student self-check, public tests only
        if not a.track: sys.exit('--track is required with --project')
        proj = find_project(a.project)
        if not proj: sys.exit('no Cargo.toml found in that folder')
        g = grade_one(proj, a.track, a.tests, ['public'])
        if g['error']: print(g['error']); sys.exit(1)
        print(feedback(g['results'], False))
        ok, words = readme_info(proj)
        print(f"\nREADME: {'found' if ok else 'MISSING'} ({words} words)")
        return

    if not a.zips: ap.error('give --zips DIR (or --project DIR --track NAME)')
    os.makedirs(a.out, exist_ok=True)
    rows = []
    zips = sorted(f for f in os.listdir(a.zips) if f.lower().endswith('.zip'))
    for i, z in enumerate(zips, 1):
        matric = os.path.splitext(z)[0]
        track = track_of(matric)
        row = dict(matric=matric, track=track or '?', built=0, public_passed=0, public_total=0, hidden_passed=0,
                   hidden_total=0, build_mark=0, public_mark=0, hidden_mark=0, readme_found='', readme_words='',
                   auto_mark_of_7=0, notes='')
        t0 = time.time()
        if not track:
            row['notes'] = 'cannot read the last digit of the file name'
            rows.append(row); continue
        work = tempfile.mkdtemp(prefix='sub_')
        try:
            try:
                with zipfile.ZipFile(os.path.join(a.zips, z)) as zf:
                    for m in zf.infolist():   # refuse paths that escape the folder
                        dest = os.path.realpath(os.path.join(work, m.filename))
                        if not dest.startswith(os.path.realpath(work)):
                            raise ValueError('unsafe path in zip')
                    zf.extractall(work)
            except Exception as e:
                row['notes'] = f'bad zip: {e}'; rows.append(row); continue
            proj = find_project(work)
            if not proj:
                row['notes'] = 'no Cargo.toml found in the zip'
            else:
                g = grade_one(proj, track, a.tests, ['public', 'hidden'])
                row['built'] = g['built']
                pub, hid = g['results']['public'], g['results']['hidden']
                row['public_passed'] = sum(1 for r in pub if r[1]); row['public_total'] = len(pub)
                row['hidden_passed'] = sum(1 for r in hid if r[1]); row['hidden_total'] = len(hid)
                row['build_mark'] = 1 if g['built'] else 0
                row['public_mark'] = round(4 * row['public_passed'] / row['public_total'], 2) if row['public_total'] else 0
                row['hidden_mark'] = round(2 * row['hidden_passed'] / row['hidden_total'], 2) if row['hidden_total'] else 0
                ok, words = readme_info(proj)
                row['readme_found'] = 'yes' if ok else 'no'; row['readme_words'] = words
                row['notes'] = (g['error'] or '').splitlines()[0] if g['error'] else ''
                txt = f"{matric}  track: {track}\nbuilt: {'yes' if g['built'] else 'NO'}\n"
                if g['error']: txt += g['error'] + '\n'
                txt += feedback(g['results'], a.hidden_detail) + f"\nREADME: {'found' if ok else 'MISSING'} ({words} words)\n"
                open(os.path.join(a.out, matric + '.txt'), 'w').write(txt)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        row['auto_mark_of_7'] = round(row['build_mark'] + row['public_mark'] + row['hidden_mark'], 2)
        rows.append(row)
        print(f"[{i}/{len(zips)}] {matric} {track}: auto {row['auto_mark_of_7']}/7 ({time.time()-t0:.0f}s)", flush=True)
    cols = ['matric','track','built','public_passed','public_total','hidden_passed','hidden_total','build_mark',
            'public_mark','hidden_mark','auto_mark_of_7','readme_found','readme_words','readme_mark_manual_1',
            'defence_manual_2','total_of_10','notes']
    with open(os.path.join(a.out, 'results.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for n, r in enumerate(rows, 2):
            r['total_of_10'] = f'=K{n}+N{n}+O{n}'   # auto + README + defence, fills in once you type the manual marks
            w.writerow(r)
    print(f'Done. {len(rows)} students. See {a.out}/results.csv')

if __name__ == '__main__':
    main()
