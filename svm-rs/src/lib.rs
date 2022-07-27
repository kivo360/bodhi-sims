use hashbrown::HashMap;
use pyo3::prelude::*;

pub mod accounts;

// #[macro_use]
// extern crate serde;

// #[macro_use]
// extern crate async_trait;

#[pyclass]
struct ItemController {
    items: HashMap<String, u32>,
}

#[pymethods]
impl ItemController {
    #[new]
    fn new() -> Self {
        ItemController {
            items: HashMap::new(),
        }
    }

    fn add_item(&mut self, name: &str, count: u32) {
        self.items.insert(name.to_string(), count);
    }

    fn __setitem__(&mut self, name: &str, count: u32) {
        // println!("{}", name);
        self.add_item(name, count);
    }

    fn __getitem__(&self, name: &str) -> u32 {
        *self.items.get(name).unwrap_or(&0)
    }
}

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn svm_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<ItemController>()?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
