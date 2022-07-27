use chrono::NaiveDate;
use hashbrown::HashMap;
use rusty_money::{iso, Money};
use serde::{de, Deserialize, Deserializer, Serialize};
use std::fmt::Display;
use std::str::FromStr;

/// root data structure that contains the deserialized `LedgerFile` data
/// and associated structs
#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct LedgerFile {
    pub currency: String,
    pub accounts: Vec<Account>,
    pub transactions: Vec<Transaction>,
}

#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct Account {
    pub account: String,
    pub amount: f64,
    pub budget_month: Option<f64>,
    pub budget_year: Option<f64>,
}

#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct Transaction {
    #[serde(deserialize_with = "deserialize_date_from_str")]
    pub date: NaiveDate,
    pub account: Option<String>,
    pub amount: Option<f64>,
    pub description: String,
    pub offset_account: Option<String>,
    pub transactions: Option<Vec<TransactionList>>,
}

fn deserialize_date_from_str<'de, S, D>(deserializer: D) -> Result<S, D::Error>
where
    S: FromStr,
    S::Err: Display,
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    S::from_str(&s).map_err(de::Error::custom)
}

#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct TransactionList {
    pub account: String,
    pub amount: f64,
}

#[derive(Debug, PartialEq)]
pub enum Group {
    Monthly,
    Yearly,
    Daily,
    None,
}

/// data structure for handling `Option` values contained
/// within the `LedgerFile` for ease of program access
#[derive(Debug, PartialEq)]
struct OptionalKeys {
    account: String,
    offset_account: String,
    amount: f64,
    transactions: Vec<TransactionList>,
}

impl OptionalKeys {
    fn match_optional_keys(transaction: &Transaction) -> Self {
        let account = match &transaction.account {
            None => "".to_string(),
            Some(name) => name.to_string(),
        };

        let offset_account = match &transaction.offset_account {
            None => "".to_string(),
            Some(name) => name.to_string(),
        };

        let amount = transaction.amount.unwrap_or(0.00);

        let transactions = match transaction.transactions.clone() {
            None => vec![],
            Some(list) => list,
        };

        Self {
            account,
            offset_account,
            amount,
            transactions,
        }
    }
}

#[derive(Debug, PartialEq)]
struct GroupMap {
    account_amount_map: HashMap<String, HashMap<String, f64>>,
}

impl GroupMap {
    fn new() -> Self {
        Self {
            account_amount_map: HashMap::new(),
        }
    }

    fn send_money(&mut self, from_account: &str, to_account: &str, amount: f64) {
        // TODO: Get back to this when you get finished seeing dad.
        // TODO: Check to see if an account exists.
        let mut from_account_map = self
            .account_amount_map
            .entry(from_account.to_string())
            .or_insert(HashMap::new());
        // let mut to_account_map = self
        //     .account_amount_map
        //     .entry(to_account.to_string())
        //     .or_insert(HashMap::new());

        // let from_amount = from_account_map
        //     .entry(to_account.to_string())
        //     .or_insert(0.00);
        // *from_amount -= amount;
        // let to_amount = to_account_map
        //     .entry(from_account.to_string())
        //     .or_insert(0.00);
        // *to_amount += amount;
    }

    fn get_account_amount(&self, account: &str) -> f64 {
        let mut total = 0.00;
        for (key, value) in self.account_amount_map.iter() {
            if key == account {
                for (_, amount) in value.iter() {
                    total += amount;
                }
            }
        }
        total
    }
}

#[cfg(test)]
mod test_super {
    use super::*;

    #[test]
    fn assign_account_vec() {
        let accounts = vec![
            Account {
                account: "asset:cash".to_string(),
                amount: 100.00,
                budget_month: None,
                budget_year: None,
            },
            Account {
                account: "expense:foo".to_string(),
                amount: 0.00,
                budget_month: None,
                budget_year: None,
            },
            Account {
                account: "expense:bar".to_string(),
                amount: 0.00,
                budget_month: None,
                budget_year: None,
            },
            Account {
                account: "expense:baz".to_string(),
                amount: 0.00,
                budget_month: None,
                budget_year: None,
            },
        ];
        assert!(accounts.len() > 0);
    }
}
