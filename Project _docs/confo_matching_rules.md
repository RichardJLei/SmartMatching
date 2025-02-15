```mermaid
flowchart TD
    A[Start Matching Process]
    B[Extract individual legs from confirmation]
    C[Enrich legs with TradingBusinessUnitCode and CounterpartyCode]
    D[Apply user-defined matching rule: TradingBusinessUnitCode, CounterpartyCode, BusinessUnitBuySell, TradingCCYAmount, TradingCurrency, SettlementCurrency, SettlementCCYAmount]
    E[Create BusinessUnitMatchingKey from leg data based on rule]
    F[Create CounterpartyMatchingKey by swapping TradingBusinessUnitCode with CounterpartyCode and reversing BusinessUnitBuySell]
    G[Search for legs where candidate.CounterpartyMatchingKey = current leg’s BusinessUnitMatchingKey]
    H{Match Result?}
    I[One-to-One Match: Mark both legs as matched & update leg table]
    J[One-to-Many Match: Flag for user resolution]
    K[No Match Found: Flag leg for review]
    L[Check if all legs in confirmation are matched]
    M[Mark entire confirmation as matched]
    N[Leave confirmation as partially matched]
    O[End Process]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H -- "One-to-One" --> I
    H -- "One-to-Many" --> J
    H -- "No Match" --> K
    I --> L
    J --> L
    K --> L
    L -- "All Matched" --> M
    L -- "Not All Matched" --> N
    M --> O
    N --> O

