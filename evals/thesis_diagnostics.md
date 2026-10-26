# Investment thesis: Diagnostics (eval fixture)

This file is the FIXED thesis the evals run against. It is the Diagnostics example of `thesis.md` (repo root), filled in.
The eval cases in `evals/cases/` are labelled against it: change it and every label may become wrong.
Your own sector thesis lives in `thesis.md` (repo root) and is used by the plugin, not by the evals.

## 1. Investment strategy
Profitable mid-sized diagnostics companies with recurring revenue (consumables, service, supply contracts) whose share
price has fallen for reasons we believe are temporary. Private ownership lets the fund finance the next product cycle,
make add-on acquisitions and fix operations away from quarterly market pressure.

## 2. Screening filters
| Filter | Field | Min | Max | Your value |
|---|---|---|---|---|
| Team | `team` | | | Diagnostics |
| Countries | `country` | | | United States, Canada, United Kingdom, Ireland, France, Germany, Switzerland, Italy, Spain, Belgium, Netherlands, Sweden, Denmark, Norway, Finland |
| Market cap (€M) | `market_cap_eur_m` | 100 | 4000 | |
| EBITDA margin | `ebitda_margin_ltm` | 0.10 | | |
| Role | `role` | | | candidate |

## 3. Judgment criteria
| Criterion | Rule | Effect |
|---|---|---|
| Segments we like | In-vitro diagnostics: instruments, assays, OEM analyzers, lab automation | Outside these segments: Radar |
| Business model | Recurring revenue (consumables, service) is at least half of sales | Warning only, never a reject |
| Why the price is low | Must be temporary: product transition, customer destocking, one-off charges. Not a structural loss of market | Structural decline: Radar |
| Ownership rule | Flag any holder above 25%: name, stake, and anything they said publicly about selling | Flag only; reject only if they ruled out a sale |
| Kill criteria | Net debt above 4x EBITDA (figure from the data, never computed by the judge); a controlling shareholder who ruled out a sale; a major unresolved regulatory issue | Reject |
| Good fit (example) | A profitable OEM instrument maker with long supply contracts, share price down sharply after a product transition, founding family holding a large stake | |
| Bad fit (example) | A loss-making genomics lab whose growth depends on reimbursement decisions | |
| Verdict | **Priority** = no kill criterion and the thesis criteria are met: we would buy at the right price. **Radar** = fits the strategy but a key fact is unknown, or the drop may be structural, or a thesis criterion is not met: keep watching. **Reject** = any kill criterion is met. An unknown fact is never a pass. **Actionable** is not a verdict: the code grants it to a Priority company whose takeout price is at or below the target price. | |

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
