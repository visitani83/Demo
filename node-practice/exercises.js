// Node.js `for` loop practice.
//
// Fill in each TODO using a `for` loop (not .map/.filter/.reduce —
// the point is to practice the loop syntax itself). Then run:
//
//   node node-practice/run.js
//
// to check your work. Compare with node-practice/solutions.js if you
// get stuck.

// 1. Classic `for` loop
// Return an array of numbers from 1 to n (inclusive), e.g. countUpTo(5) -> [1,2,3,4,5]
function countUpTo(n) {
  const result = [];
  // TODO: use a for loop to push 1..n into result
  return result;
}

// 2. Accumulating a value
// Return the sum of all numbers from 1 to n (inclusive), e.g. sumUpTo(5) -> 15
function sumUpTo(n) {
  let total = 0;
  // TODO: use a for loop to add each number to total
  return total;
}

// 3. Stepping / skipping
// Return an array of even numbers from 0 to n (inclusive), e.g. evensUpTo(10) -> [0,2,4,6,8,10]
function evensUpTo(n) {
  const result = [];
  // TODO: use a for loop with a step of 2
  return result;
}

// 4. FizzBuzz — classic loop + branching practice
// Return an array of strings for numbers 1..n where:
//  - multiples of 3 -> "Fizz"
//  - multiples of 5 -> "Buzz"
//  - multiples of both -> "FizzBuzz"
//  - otherwise -> the number as a string
function fizzBuzz(n) {
  const result = [];
  // TODO: use a for loop + if/else
  return result;
}

// 5. Looping over an array with for...of
// Return the largest number in the array using a for...of loop
function findMax(numbers) {
  let max = -Infinity;
  // TODO: use for...of to find the max
  return max;
}

// 6. Looping backwards
// Return a new array with the elements of `arr` in reverse order,
// using a for loop that counts down (don't use .reverse()!)
function reverseArray(arr) {
  const result = [];
  // TODO: use a for loop counting from the end to the start
  return result;
}

// 7. Nested for loops
// Return a string that draws a square of `size` rows and `size` columns of "*",
// each row separated by "\n". E.g. drawSquare(3) ->
// "***\n***\n***"
function drawSquare(size) {
  let output = '';
  // TODO: use a nested for loop (outer = rows, inner = columns)
  return output;
}

module.exports = {
  countUpTo,
  sumUpTo,
  evensUpTo,
  fizzBuzz,
  findMax,
  reverseArray,
  drawSquare,
};
