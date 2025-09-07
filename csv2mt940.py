#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv2mt940 – Convert a ';'-separated TopCard Switzerland CSV file into MT940 .sta format

USAGE (on macOS Terminal):
    python3 csv2mt940.py input.csv output.sta

    # with StarMoney profile (recommended for import):
    python3 csv2mt940.py -p starmoney input.csv output.sta

    # with debug table:
    python3 csv2mt940.py -d input.csv output.sta

    # only first 10 transactions:
    python3 csv2mt940.py -p starmoney --limit 10 input.csv output.sta

REQUIREMENTS:
    - macOS or Linux with Python 3.9+ (use `python3 --version` to check)
    - No extra Python packages required (only standard library)

OPTIONAL SETUP (macOS):
    - Install Homebrew if not present: https://brew.sh
    - Install Python 3:   brew install python
    - Make script executable (once):
        chmod +x csv2mt940.py
      Then run it directly:
        ./csv2mt940.py input.csv output.sta

        
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import sys, os, re, csv, io, datetime, argparse
from typing import List

def print_table(rows: List[List[str]], headers: List[str]) -> None:
    cols = list(zip(*([headers] + rows))) if rows else [headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    def fmt(row): return " | ".join(str(c).ljust(w) for c, w in zip(row, widths))
    line = "-+-".join("-"*w for w in widths)
    print(fmt(headers)); print(line); [print(fmt(r)) for r in rows]

def fail(msg: str, exit_code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr); sys.exit(exit_code)

def wrap_86(text: str, width: int = 65, max_lines: int = 6) -> List[str]:
    clean = " ".join(text.split())
    lines = [clean[i:i+width] for i in range(0, len(clean), width)] or [""]
    return lines[:max_lines]

def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="csv2mt940",
        description="Convert ';'-CSV to MT940 .sta (StarMoney-friendly with -p starmoney)."
    )
    p.add_argument("input_csv", nargs="?", help="Path to input CSV")
    p.add_argument("output_sta", nargs="?", help="Path to output MT940 (.sta)")
    p.add_argument("--encoding", default="iso-8859-1", help="CSV encoding (default: iso-8859-1)")
    p.add_argument("--delimiter", default=";", help="CSV delimiter (default: ';')")
    p.add_argument("--limit", type=int, default=0, help="Process first N rows only (0=all)")

    # short and long forms
    p.add_argument("-d", "--debug", action="store_true",
                   help="Verbose table output (cannot be combined with --profile)")
    p.add_argument("-p", "--profile", choices=["starmoney", "plain"], default=None,
                   help="Output profile tweaks. Cannot be combined with --debug.")

    p.add_argument("--ttype", default="NTRF", help="MT940 :61 transaction code (default NTRF)." )
    p.add_argument("--eref", default="NONREF", help="EREF+ value for :86: (default NONREF)" )
    p.add_argument("--purp", default="", help="PURP+ (optional SEPA purpose code) for :86:" )
    p.add_argument("--suppress-balances", action="store_true",
                   help="Do not write :60F/:62F balances (some tools ignore them)")

    if len(argv) == 0:
        print("usage: csv2mt940 input.csv output.mt940.sta", file=sys.stderr)
        print("MISSING PARAMETERS: input_csv, output_sta", file=sys.stderr)
        p.print_help(sys.stderr)
        sys.exit(2)

    args = p.parse_args(argv)

    # enforce exclusivity of --debug and --profile
    if args.debug and args.profile:
        fail("Options --debug (-d) and --profile (-p) cannot be used together. Choose either debug mode or a profile.")

    # validate input/output
    missing = [name for name, val in (("input_csv", args.input_csv), ("output_sta", args.output_sta)) if not val]
    if missing:
        print("usage: csv2mt940 input.csv output.mt940.sta", file=sys.stderr)
        print(f"MISSING PARAMETERS: {', '.join(missing)}", file=sys.stderr)
        p.print_help(sys.stderr); sys.exit(2)

    if not os.path.isfile(args.input_csv):
        fail("Input CSV not found.\n"
             f"  Searched: {args.input_csv}\n"
             f"  Absolute: {os.path.abspath(args.input_csv)}\n"
             f"  CWD:      {os.getcwd()}\n"
             "Verify path (case, extension, permissions)." )
    out_dir = os.path.dirname(os.path.abspath(args.output_sta)) or "."
    if not os.path.isdir(out_dir):
        fail("Output directory does not exist.\n"
             f"  Given: {args.output_sta}\n"
             f"  Expected dir: {out_dir}")
    return args

def main(argv: List[str]) -> None:
    args = parse_args(argv)

    try:
        csvFile = open(args.input_csv, "r", encoding=args.encoding, newline="")
    except Exception as e:
        fail("Failed to open input CSV.\n"
             f"  File: {args.input_csv}\n"
             f"  Absolute: {os.path.abspath(args.input_csv)}\n"
             f"  Encoding attempt: {args.encoding}\n"
             f"  Error: {type(e).__name__}: {e}" )

    try:
        mt940File = io.open(args.output_sta, "w", encoding="utf-8", newline="")
    except Exception as e:
        fail("Failed to create/open output file.\n"
             f"  File: {args.output_sta}\n"
             f"  Absolute: {os.path.abspath(args.output_sta)}\n"
             f"  Error: {type(e).__name__}: {e}" )

    print("----- > Start processing")
    reader = csv.reader(csvFile, delimiter=args.delimiter)

    lineNumber = 0
    tx_count = 0
    bodies: List[str] = []
    header = ""
    opening_date = ""
    closing_date = ""
    currency_fallback = "EUR"

    debug_rows: List[List[str]] = []

    try:
        for row in reader:
            lineNumber += 1
            if lineNumber < 3:
                continue
            if not row or all(c.strip() == "" for c in row):
                continue
            joined = args.delimiter.join(row).strip()
            if joined.startswith(f"{args.delimiter*4}Total"):
                continue

            needed_idx = [1,3,4,5,7,10,11,12]
            if len(row) <= max(needed_idx):
                fail("CSV row has too few columns.\n"
                     f"  Line (incl. header): {lineNumber}\n"
                     f"  Columns: {len(row)} Needed: >= {max(needed_idx)+1}\n"
                     f"  Row: {joined}")

            booking = row[12].strip()
            valuta  = row[3].strip()
            comment = row[4].strip()
            tags    = row[5].strip()
            account = row[1].strip()
            curr    = row[7].strip() or currency_fallback
            amt     = row[10].strip()
            amt_alt = row[11].strip()

            def date_parts(d: str) -> tuple:
                if len(d) >= 10 and d[2] == "." and d[5] == ".":
                    return d[8:10], d[3:5], d[0:2]
                fail("Unexpected date format (expected DD.MM.YYYY).\n"
                     f"  Line: {lineNumber}\n  Value: '{d}'")
            yy_b, mm_b, dd_b = date_parts(booking)
            yy_v, mm_v, dd_v = date_parts(valuta)

            eref = args.eref or "NONREF"
            svwz = comment
            purp = args.purp.strip()

            val = amt if amt.strip() else amt_alt
            if not val.strip():
                fail("Neither amount (col 10) nor amountC (col 11) has a value.\n"
                     f"  Line: {lineNumber}\n  Row: {joined}")
            dc = "D"
            if not amt.strip() and amt_alt.strip():
                dc = "C"
            val = val.replace(".", ",")  # SWIFT uses comma decimals

            if not header:
                now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                header  = f":20:DateOfConversion{now}\r\n"
                header += f":25:{account}\r\n"
                header += ":28C:00001/001\r\n"
                closing_date = f"{dd_v}{mm_v}{yy_v}"

            ttype = args.ttype.strip().upper() if args.profile == "starmoney" else "FCHG"
            body  = f":61:{yy_v}{mm_v}{dd_v}{mm_b}{dd_b}{dc}{val}{ttype}NONREF//NONREF\r\n"

            if args.profile == "starmoney":
                parts_86 = []
                first_line = f"EREF+{eref}"
                if purp: first_line += f" PURP+{purp}"
                parts_86.extend(wrap_86(first_line, 65, 6))
                sv_lines = wrap_86(f"SVWZ+{svwz}" if svwz else "SVWZ+", 65, 6 - len(parts_86))
                parts_86.extend(sv_lines)
                body += ":86:" + ("\r\n".join(parts_86)) + "\r\n"
            else:
                parts_86 = wrap_86(comment or "", 65, 6)
                tag_list = [t.strip() for t in (tags.split(",") if tags else []) if t.strip()]
                tag_text = ("; ".join(tag_list)) if tag_list else ""
                lines = [l for l in parts_86 if l] + ([tag_text] if tag_text else [])
                body += (":86:" + ("\r\n".join(lines)) + "\r\n")

            bodies.append(body)
            tx_count += 1
            opening_date = f"{dd_v}{mm_v}{yy_v}"

            if args.debug:
                debug_rows.append([str(lineNumber), valuta, booking, dc, val, curr,
                                   (comment[:32] + "…") if len(comment) > 33 else comment])

            if args.limit and tx_count >= args.limit:
                break
    finally:
        csvFile.close()

    mt940File.write("\ufeff")
    mt940File.write(header)
    if not args.suppress_balances:
        mt940File.write(f":60F:C{opening_date}{curr}0,0\r\n")
    for i in range(tx_count, 0, -1):
        mt940File.write(bodies[i-1])
    if not args.suppress_balances:
        mt940File.write(f":62F:C{closing_date}{curr}0,0\r\n")
    mt940File.write("\r\n")
    mt940File.close()

    print("----- < end processing")
    print("----- | end conversion")
    if args.debug:
        print("\nDEBUG SUMMARY (first rows):")
        print_table(debug_rows, headers=["Line#","Value date","Booking date","D/C","Amount","CCY","Comment"])
        print(f"\nTotal bookings processed: {tx_count}")

if __name__ == "__main__":
    main(sys.argv[1:])
