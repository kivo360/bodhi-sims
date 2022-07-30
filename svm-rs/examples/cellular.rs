extern crate rand;
use rand::{distributions::*, *};
use std::fmt;
use std::{thread, time};

#[derive(Copy, Clone)]
enum ForestState {
    Tree(u8),
    Ground,
    Fire(u8),
    Smouldering,
}

use std::iter::FromIterator;
use ForestState::*;

// LENGTH and WIDTH const usize
const LENGTH: usize = 30;
const WIDTH: usize = 15;

struct Forest([[ForestState; LENGTH]; WIDTH]);

type Neighborhood = [ForestState; 9];

const NEIGHBORHOOD: [(i64, i64); 9] = [
    (-1, -1),
    (0, 1),
    (1, 1),
    (-1, 0),
    (0, 0),
    (1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
];

fn update(n: Neighborhood) -> ForestState {
    match n[4] {
        Tree(size) => {
            let surround_count = n
                .iter()
                .filter(|x| match x {
                    Fire(_) => true,
                    _ => false,
                })
                .count() as f32;

            if surround_count >= 4.0 / (size as f32) {
                Fire(size)
            } else {
                Tree(size)
            }
        }
        Fire(1) => Smouldering,
        Fire(size) => Fire(size - 1),
        state => state,
    }
}

fn step(forest: Forest) -> Forest {
    forest.into_iter().map(update).collect()
}

struct ForestIterator {
    forest: Forest,
    x: usize,
    y: usize,
}

impl Iterator for ForestIterator {
    type Item = Neighborhood;

    fn next(&mut self) -> Option<Self::Item> {
        let Forest(forest) = self.forest;

        match (self.x, self.y) {
            // Waiting room for inclusive range patterns
            (0..=WIDTH, 0..=LENGTH) if (self.x, self.y) != (WIDTH, LENGTH) => {
                let mut neighborhood = [Ground; 9];

                for (i, (x, y)) in NEIGHBORHOOD.iter().enumerate() {
                    let x_p = x + self.x as i64;
                    let y_p = y + self.y as i64;

                    if x_p >= 0 && x_p < WIDTH as i64 && y_p >= 0 && y_p < LENGTH as i64 {
                        neighborhood[i] = forest[x_p as usize][y_p as usize];
                    }
                }

                self.x += 1;
                if self.x >= WIDTH {
                    self.x = 0;
                    self.y += 1;
                }
                Some(neighborhood)
            }
            _ => None,
        }
    }
}

impl IntoIterator for Forest {
    type Item = Neighborhood;
    type IntoIter = ForestIterator;

    fn into_iter(self) -> Self::IntoIter {
        ForestIterator {
            forest: self,
            x: 0,
            y: 0,
        }
    }
}

impl FromIterator<ForestState> for Forest {
    fn from_iter<T>(iter: T) -> Self
    where
        T: IntoIterator<Item = ForestState>,
    {
        let mut forest = [[Ground; LENGTH]; WIDTH];

        let mut x = 0;
        let mut y = 0;

        for cell in iter {
            forest[x][y] = cell;
            x += 1;
            if x >= WIDTH {
                x = 0;
                y += 1;
                if y >= LENGTH {
                    break;
                }
            }
        }
        // This conversion works because forest is already a struct of [[ForestState; LENGTH]; WIDTH]
        // x, y are being defined using the constants, LENGTH]; WIDTH.
        Forest(forest)
    }
}

///
///impl Distribution<ForestState> for Standard {
///    fn sample<R : Rng + ?Sized>(&self, rng: &mut R) -> ForestState {
///        match rng.gen_range(0, 6) {
///            0 => Ground,
///            x => Tree(x)
///        }
///    }
///}
///

impl Distribution<ForestState> for Standard {
    fn sample<R: Rng + ?Sized>(&self, rng: &mut R) -> ForestState {
        match rng.gen_range(0..6) {
            0 => Ground,
            x => Tree(x),
        }
    }
}

impl fmt::Display for Forest {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let Forest(forest) = self;

        for row in forest.iter() {
            for cell in row.iter() {
                let ch = match cell {
                    Ground => ' ',
                    Smouldering => '.',
                    Fire(1..=2) => 'f',
                    Fire(_) => 'F',
                    Tree(1..=2) => 't',
                    Tree(_) => 'T',
                };

                write!(f, "{}", ch)?;
            }

            write!(f, "\n")?;
        }

        Ok(())
    }
}

fn main() {
    // [[ForestState; LENGTH]; WIDTH] is a doubly nested array
    let mut rng = rand::thread_rng();

    print!("\x1b[2J\x1b[?25l");

    // Grow the forest
    let mut forest: Forest = (&mut rng)
        .sample_iter(Standard)
        .take(LENGTH * WIDTH)
        .collect();

    // Light a fire
    forest.0[rng.gen_range(0..WIDTH)][rng.gen_range(0..LENGTH)] = Fire(5);

    // Watch it burn
    loop {
        print!("\x1b[;H");

        println!("{}", forest);
        forest = step(forest);

        thread::sleep(time::Duration::from_millis(100));
    }
}
