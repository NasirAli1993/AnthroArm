"""Explicit manual serial console for the one-finger demonstrator.
No board is selected automatically and nothing is armed on startup.
Run with --dry-run to inspect the protocol without any hardware access.
"""
import argparse,threading,time

def validate(text):
    text=text.strip().upper()
    if text in ('ARM','DISARM','STATUS','KEEPALIVE'):return text
    parts=text.split()
    if len(parts)==2 and parts[0]=='SET' and parts[1].isdigit() and 1450<=int(parts[1])<=1550:return 'SET '+str(int(parts[1]))
    raise ValueError('Use ARM, SET 1450..1550, STATUS, DISARM or QUIT')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',help='Explicit board port, e.g. COM5; never guessed')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    if not args.dry_run and not args.port:parser.error('Supply --port or use --dry-run; hardware is never auto-selected')
    if args.dry_run:
        for line in ('STATUS','ARM','SET 1520','KEEPALIVE','DISARM'):
            print('Would send:',validate(line))
        print('Dry run complete. No board opened.');return
    import serial
    active=threading.Event();stop=threading.Event();mutex=threading.Lock()
    with serial.Serial(args.port,115200,timeout=.1,write_timeout=.5) as board:
        def send(line):
            with mutex:board.write((line+'\n').encode('ascii'));board.flush()
        def worker():
            previous=0
            while not stop.is_set():
                if active.is_set() and time.monotonic()-previous>.25:send('KEEPALIVE');previous=time.monotonic()
                line=board.readline().decode('ascii',errors='replace').strip()
                if line:
                    print('\nBoard:',line)
                    if line.startswith(('DISARMED','WATCHDOG','ERROR','READY')):active.clear()
                time.sleep(.01)
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        print('Board starts disarmed. Verify loose tendon, power wiring and E-stop before ARM. QUIT exits.')
        try:
            while True:
                line=input('servo> ').strip().upper()
                if line=='QUIT':break
                try:line=validate(line)
                except ValueError as e:print(e);continue
                if line=='ARM':active.set()
                if line=='DISARM':active.clear()
                send(line)
        finally:
            active.clear()
            try:send('DISARM')
            finally:stop.set();thread.join(timeout=1)

if __name__=='__main__':main()
