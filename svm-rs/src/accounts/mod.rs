// #![deny(missing_docs)]
// //! A simple in memory account and transaction system
// //!
use anyhow::Result;
use anyhow::{anyhow, ensure};
use hashbrown::HashMap;
use serde::{Deserialize, Serialize};
// use rusty_money::Money;

/// A way to create a custom enum type.
#[derive(Debug, Serialize, Deserialize)]
pub enum Reason {
    /// A way to create a custom enum type.
    Basic,
    /// A way to create a custom enum type.
    Detailed(String),
}

impl Reason {
    fn msg(&self) -> String {
        match self {
            Reason::Basic => "Payment succeeded".to_string(),
            Reason::Detailed(msg) => msg.to_string(),
        }
    }
}
/// A way to create a custom enum type.
pub enum Command {
    /// Sending money transaction between two accounts.
    Money(String, String, f64, Reason),
    /// We're logging a record inside the a key value store.
    KeyLog,
}

/// root data structure that contains the deserialized `LedgerFile` data
/// and associated structs
// #[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct Ledger {
    currency: String,
    /// accounts are a key value store of all accounts within the database.
    pub accounts: HashMap<String, Account>,
    /// transactions are a key value store of all transactions within the database.
    pub transactions: Vec<Transaction>,
}

impl Ledger {
    pub fn new(currency: String) -> Self {
        Self {
            currency,
            accounts: HashMap::new(),
            transactions: vec![],
        }
    }

    pub fn add_account(&mut self, account: Account) {
        self.accounts.insert(account.account.clone(), account);
    }

    pub fn add_accounts(&mut self, accounts: Vec<Account>) {
        for account in accounts {
            self.add_account(account);
        }
    }

    pub fn command(&mut self, command: Command) -> Result<()> {
        match command {
            Command::Money(from, to, amount, reason) => {
                let response = self.transfer_money(&from, &to, amount, reason);
                let is_error = match response {
                    Ok(_) => Ok(()),
                    Err(e) => Err(e),
                };
                return is_error;
            }
            Command::KeyLog => return Ok(()),
        }
        // Ok(())
        // self.transactions.push(transaction);
    }

    pub fn transfer_money(
        &mut self,
        from: &str,
        to: &str,
        amount: f64,
        reason: Reason,
    ) -> Result<()> {
        let mut transaction = Transaction::new(0, from.to_string(), to.to_string(), amount, reason);
        if !self.accounts.contains_key(from) {
            transaction.status = false;
            self.transactions.push(transaction.clone());
            return Err(anyhow!("The origin account does not exist"))?;
        };
        // let to_account = self.accounts.get_mut(to);
        if !self.accounts.contains_key(to) {
            transaction.status = false;
            self.transactions.push(transaction.clone());
            return Err(anyhow!("The to account does not exist"))?;
        };
        let mut is_raise = false;
        self.accounts.entry_ref(from).and_modify(|acc| {
            match acc.withdraw(amount) {
                Ok(_) => (),
                Err(_e) => {
                    is_raise = true;
                    return ();
                }
            };
        });
        if is_raise {
            transaction.status = false;
            self.transactions.push(transaction.clone());
            return Err(anyhow!("The origin account does not have enough money"))?;
        }
        self.accounts.entry_ref(to).and_modify(|acc| {
            acc.deposit(amount);
        });
        transaction.status = true;
        self.transactions.push(transaction);
        Ok(())
    }

    fn sizeof(&self) -> usize {
        self.accounts.len()
    }
}

#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct Account {
    pub account: String,
    pub amount: f64,
}
impl Account {
    pub fn new(account: String, amount: f64) -> Self {
        Self { account, amount }
    }
    pub fn deposit(&mut self, amount: f64) {
        self.amount += amount;
    }
    pub fn withdraw(&mut self, amount: f64) -> Result<()> {
        ensure!(self.amount >= amount, "Insufficient funds");

        self.amount -= amount;
        println!("withdraw: {:?}", self.amount);
        Ok(())
    }
}

#[derive(Debug, PartialEq, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub step: i64,
    pub account: Option<String>,
    pub status: bool,
    pub amount: Option<f64>,
    pub description: String,
    pub from_account: Option<String>,
    pub transactions: Option<Vec<TransactionList>>,
}

impl Transaction {
    pub fn new(step: i64, from: String, to: String, amount: f64, reason: Reason) -> Self {
        Self {
            step: step,
            account: Some(to),
            status: true,
            amount: Some(amount),
            description: format!("{}", reason.msg()),
            from_account: Some(from),
            transactions: None,
        }
    }
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

#[cfg(test)]
mod test_super {

    use super::*;

    fn get_test_accounts() -> Vec<Account> {
        vec![
            Account::new("C".to_string(), 100.0),
            Account::new("D".to_string(), 200.0),
        ]
    }

    fn init_ledger() -> Ledger {
        let mut ledger = Ledger::new("USD".to_string());
        ledger.add_accounts(get_test_accounts());
        ledger
    }

    #[test]
    #[should_panic]
    fn test_incorrect_money_amount() {
        let mut ledger = init_ledger();
        let account = Account::new("A".to_string(), 100.0);
        ledger.add_account(account.clone());
        let mut changable = account.to_owned();
        changable.withdraw(1000.0).unwrap();
        assert_eq!(changable.amount, 90.0);
    }

    #[test]
    fn test_correct_money_transfer_amount() {
        // Less than the amount in the account
        let account = Account::new("A".to_string(), 100.0);
        let mut changable = account.to_owned();
        changable.withdraw(10.0).unwrap();
        assert_eq!(changable.amount, 90.0);
    }

    #[test]
    fn test_ledger_adds_accounts() {
        let mut ledger = init_ledger();
        let account = Account::new("A".to_string(), 100.0);
        let account2 = Account::new("B".to_string(), 100.0);

        ledger.add_account(account);
        ledger.add_account(account2);

        assert!(ledger.sizeof() > 0);

        assert_eq!(ledger.sizeof(), 4);
        // assert!(true);
    }

    #[test]
    fn test_assign_group() {
        let from_account = "from_account";
        let to_account = "from_account";
        let amount = 80.00;

        let _transaction = Transaction {
            status: false,
            step: 0 as i64,
            account: Some(from_account.to_string()),
            amount: Some(amount),
            description: "This is a test transaction".to_string(),
            from_account: Some(to_account.to_string()),
            transactions: None,
        };
    }

    #[test]
    fn assign_account_vec() {
        let accounts = get_test_accounts();
        assert!(accounts.len() > 0);
    }
}
