# csv2mt940

Convert **TopCard Service Switzerland** credit-card CSV to **MT940** for double-entry accounting and personal finance tools such as **Banana Accounting (CH)** and **StarMoney** (import).

- Pure Python 3 (no extra packages required)
- macOS / Linux / Windows compatible
- StarMoney-optimized profile writes SEPA keys in `:86:` (`EREF+`, `SVWZ+`, optional `PURP+`) and standard `:61` codes (e.g., `NTRF`)

---

## Quick Start (macOS)

```bash
# 1) Make sure Python 3 is installed
python3 --version

# 2) Clone the repository
git clone https://github.com/worryboy/csv2mt940.git
cd csv2mt940

# 3) Run conversion (StarMoney import optimized)
python3 csv2mt940.py -p starmoney input.csv output.sta
```

Optional setup on macOS:

```bash
# Install Homebrew (if not already installed): https://brew.sh
brew install python
```

---

## Usage

```bash
python3 csv2mt940.py [OPTIONS] input.csv output.sta
```

**Important:** `-p/--profile` and `-d/--debug` **cannot** be used together.  
Choose either a profile **or** debug mode.

---

## Main options

| Short | Long form             | Description |
|------:|-----------------------|-------------|
| `-p`  | `--profile`           | Output profile: `starmoney`, `plain` |
| `-d`  | `--debug`             | Debug table output |
|       | `--encoding`          | CSV encoding (default: `iso-8859-1`) |
|       | `--delimiter`         | CSV delimiter (default: `;`) |
|       | `--limit N`           | Process only first `N` rows |
|       | `--ttype CODE`        | Transaction type in `:61` (default: `NTRF` in starmoney mode) |
|       | `--eref VALUE`        | `EREF+` value for :86: (default: `NONREF`) |
|       | `--purp CODE`         | Optional `PURP+` code for :86: |
|       | `--suppress-balances` | Skip writing :60F/:62F balances |

---

## Examples

**1) StarMoney import (recommended)**  
```bash
python3 csv2mt940.py -p starmoney input.csv output.sta
```

**2) Plain MT940 (generic)**  
```bash
python3 csv2mt940.py -p plain input.csv output.sta
```

**3) Debug mode**  
```bash
python3 csv2mt940.py -d input.csv output.sta
```

**4) Only first 10 transactions**  
```bash
python3 csv2mt940.py -p starmoney --limit 10 input.csv output.sta
```

**5) UTF-8 CSV, custom type and EREF**  
```bash
python3 csv2mt940.py -p starmoney --encoding utf-8 --ttype NMSC --eref E2E123 input.csv output.sta
```

---

## CSV assumptions (TopCard CH)

Expected columns (0-based):

- [1] account number  
- [3] value date (`DD.MM.YYYY`)  
- [4] comment / purpose text  
- [5] tags (comma-separated)  
- [7] currency (EUR, CHF …)  
- [10] amount debit/credit  
- [11] alternate amount (used if col 10 empty)  
- [12] booking date (`DD.MM.YYYY`)  

Other notes:
- First 2 header rows are skipped automatically  
- Footer lines starting with `;;;;Total` are ignored  
- Either col 10 or col 11 must contain the amount  

---

## Notes for StarMoney

- `:86:` contains SEPA keys so StarMoney can parse fields cleanly:  
  - `EREF+` → End-to-End reference  
  - `SVWZ+` → Purpose / comment text  
  - `PURP+` → Optional SEPA purpose code  
- `:61` uses standard SWIFT codes (default `NTRF`, can be changed with `--ttype`)  
- Comma `,` is used as decimal separator (required by MT940 spec)  
- Balances (`:60F`/`:62F`) are optional and can be suppressed with `--suppress-balances`  
- Best results in StarMoney 14+ with `-p starmoney` profile  

---

## Git workflow (master branch)

Clone once:
```bash
git clone https://github.com/worryboy/csv2mt940.git
cd csv2mt940
```


---

## License

GNU GENERAL PUBLIC LICENSE  
Version 3, 29 June 2007

See the [LICENSE](LICENSE) file for full details.
