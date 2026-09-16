#!/usr/bin/env python3
import argparse, csv, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv_file'); args=ap.parse_args()
    rows=list(csv.DictReader(open(args.csv_file,encoding='utf-8-sig')))
    if not rows: raise SystemExit('No pilot rows')
    def b(v): return str(v).strip().lower() in ('1','true','yes','si','sí')
    first=sum(b(r.get('first_mission_without_adult')) for r in rows)/len(rows)*100
    next_action=sum(b(r.get('identified_next_action')) for r in rows)/len(rows)*100
    critical=sum(int(r.get('critical_navigation_errors') or 0) for r in rows)
    sat=sum(float(r.get('satisfaction_1_5') or 0) for r in rows)/len(rows)
    privacy=sum(int(r.get('critical_privacy_incidents') or 0) for r in rows)
    checks={'first_mission_without_adult_pct':round(first,1),'identified_next_action_pct':round(next_action,1),'critical_navigation_errors':critical,'average_satisfaction':round(sat,2),'critical_privacy_incidents':privacy}
    passed=first>=90 and next_action>=95 and critical<=max(1,len(rows)*0.05) and sat>=4 and privacy==0
    print(json.dumps({'participants':len(rows),'metrics':checks,'pilot_acceptance':passed},indent=2)); raise SystemExit(0 if passed else 2)
if __name__=='__main__': main()
