# Phase 1 Calculation Map

## 1. Engineering schedule drives financial timing

Each site is governed by six dated milestones: site control, design completion, construction start, power ready, commissioning, and ready for service. Scenario delays shift every milestone consistently.

## 2. Milestone-based CapEx

Each CapEx category is assigned to a physical delivery interval and distributed with a triangular spend curve:

- land and site preparation: site control through design;
- shell and construction: construction start through power ready;
- utility, electrical, and mechanical systems: construction start through power ready with later weighting;
- networking and storage: power ready through commissioning;
- GPUs and compute: power ready through ready for service;
- fees and contingency: spread across development and commissioning.

The monthly category schedules reconcile exactly to each site's total CapEx plan.

## 3. Power, commissioning, and RFS gates

No GPU capacity, revenue, or operating load is recognized before ready for service. Power-ready and commissioning dates remain visible control gates in the monthly output.

## 4. GPU deployment and utilization

GPU capacity phases in linearly over each site's `gpu_ramp_months`. Utilization then ramps from the ready-for-service level to mature utilization over `months_to_mature`.

## 5. Revenue and OpEx

Revenue equals sold GPU-hours multiplied by scenario-adjusted price per GPU-hour. OpEx includes facility power, fixed site OpEx, and variable operating cost per sold GPU-hour.

## 6. Financing and debt service

Minimum equity is funded first. Remaining CapEx follows the target debt/equity mix. Interest during construction is capitalized before RFS; afterward, cash interest and straight-line principal repayment begin.

## 7. Cash and liquidity

Portfolio cash begins with configured starting cash. Monthly operating cash flow, CapEx, financing draws, and debt service determine cash before support. Incremental funding raises preserve the minimum-cash threshold and are reported explicitly.

## 8. Returns

Site outputs include unlevered NPV, unlevered IRR, equity IRR, horizon ROIC, revenue-to-CapEx, and an illustrative terminal value based on final-year EBITDA.
