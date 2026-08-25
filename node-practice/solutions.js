// Reference solutions for node-practice/exercises.js.
// Try to solve each exercise yourself first!

function countUpTo(n) {
  const result = [];
  for (let i = 1; i <= n; i++) {
    result.push(i);
  }
  return result;
}

function sumUpTo(n) {
  let total = 0;
  for (let i = 1; i <= n; i++) {
    total += i;
  }
  return total;
}

function evensUpTo(n) {
  const result = [];
  for (let i = 0; i <= n; i += 2) {
    result.push(i);
  }
  return result;
}

function fizzBuzz(n) {
  const result = [];
  for (let i = 1; i <= n; i++) {
    if (i % 15 === 0) {
      result.push('FizzBuzz');
    } else if (i % 3 === 0) {
      result.push('Fizz');
    } else if (i % 5 === 0) {
      result.push('Buzz');
    } else {
      result.push(String(i));
    }
  }
  return result;
}

function findMax(numbers) {
  let max = -Infinity;
  for (const num of numbers) {
    if (num > max) {
      max = num;
    }
  }
  return max;
}

function reverseArray(arr) {
  const result = [];
  for (let i = arr.length - 1; i >= 0; i--) {
    result.push(arr[i]);
  }
  return result;
}

function drawSquare(size) {
  let output = '';
  for (let row = 0; row < size; row++) {
    let line = '';
    for (let col = 0; col < size; col++) {
      line += '*';
    }
    output += row === 0 ? line : '\n' + line;
  }
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
