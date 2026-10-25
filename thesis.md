# Investment thesis: <your team>

Fill in **Your value** (Part 3, the `thesis` skill does it with you). Blank = skipped. The code reads section 2
(`p2p/screen.py`); the judge reads sections 1 and 3 (`p2p/judge.py`). **Example** is the Diagnostics team, as an
illustration only. The evals do NOT read this file: they use `evals/thesis_diagnostics.md`.

## 1. Investment strategy
In 3 to 5 lines: what kind of listed company you would take private, and why it would be better off with your fund.

> **Your answer:**
>

> *Example:* Profitable mid-sized diagnostics companies with recurring revenue (consumables, service, supply contracts)
> whose share price has fallen for reasons we believe are temporary. Private ownership lets the fund finance the next
> product cycle, make add-on acquisitions and fix operations away from quarterly market pressure.

## 2. Screening filters
Hard numbers applied by code to `data/companies.csv`. A company outside any filter leaves the radar.
Numbers go in **Min / Max** (margin as a fraction: 0.10 = 10%); lists go in **Your value**. Blank = filter off.

| Filter | Field | Min | Max | Your value | Example |
|---|---|---|---|---|---|
| Team | `team` | | | | Diagnostics |
| Countries | `country` | | | | United States, Canada, United Kingdom, Ireland, France, Germany, Switzerland, Italy, Spain, Belgium, Netherlands, Sweden, Denmark, Norway, Finland (names as in the data) |
| Market cap (€M) | `market_cap_eur_m` | | | | Min 100, Max 4000 |
| EBITDA margin | `ebitda_margin_ltm` | | | | Min 0.10 |
| Role | `role` | | | | candidate (consolidators are never targets) |

## 3. Judgment criteria
What only a person, or the judge reading the facts, can decide. Write rules a colleague could apply without you.

| Criterion | Your rule | Example | Effect |
|---|---|---|---|
| Segments we like | | In-vitro diagnostics: instruments, assays, OEM analyzers, lab automation | Outside these segments: Radar |
| Business model | | Recurring revenue (consumables, service) is at least half of sales | Warning only, never a reject |
| Why the price is low | | Must be temporary: product transition, destocking, one-off charges. Not a structural loss of market | Structural decline: Radar |
| Ownership rule | | Flag any holder above 25%: name, stake, public statements about selling | Flag only; reject only if they ruled out a sale |
| Kill criteria | | Net debt above 4x EBITDA (from the data, never computed by the judge); a controlling shareholder who ruled out a sale; a major unresolved regulatory issue | Reject |
| Good fit (one example) | | A profitable OEM instrument maker with long supply contracts, share price down after a product transition, founding family with a large stake | |
| Bad fit (one example) | | A loss-making genomics lab whose growth depends on reimbursement decisions | |
| Verdict | keep or rewrite | **Priority** = no kill criterion and the criteria are met: we would buy at the right price. **Radar** = fits the strategy but a key fact is unknown, the drop may be structural, or a criterion is not met: keep watching. **Reject** = any kill criterion. An unknown fact is never a pass. **Actionable** is not a verdict: the code grants it to a Priority company whose takeout price is at or below the target price (section 4). | |

## 4. Valuation settings
How the target price is computed (`p2p/target_price.py`, method in `docs/target-price.md`). Blank or `default` keeps the default.
Code only: the judge never sees this section.

| Setting | In plain words | Default | Your value |
|---|---|---|---|
| Target price method | `lbo` (ability to pay), `multiple`, or `lower` of the two | `lbo` | |
| Reference multiple | The sector's usual EV / EBITDA | 13x | |
| Target IRR | Yearly return the fund needs on its equity | 25% | |
| Holding period | Years before we sell | 5 | |
| Leverage | Debt raised at entry, in years of EBITDA | 4.0x | |
| Exit multiple | EV / EBITDA assumed when we sell | 12x | |
| Revenue growth | Per year, during the holding period | 5% | |
| Exit EBITDA margin | Margin reached by the exit year; blank = today's margin | today's margin | |
| Cash conversion | Share of EBITDA left as cash after tax, capex and working capital | 50% | |
| Interest rate | On the acquisition debt | 7.5% | |
| Fees | Deal costs, % of EV | 3% | |
| Control premium | What we pay above the share price | 30% | |
| Near threshold | Actionable when takeout ≤ target price × (1 + this) | 5% | |
