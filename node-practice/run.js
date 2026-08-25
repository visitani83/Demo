// Checks your solutions in exercises.js against expected output.
//
//   node node-practice/run.js            # checks exercises.js (your work)
//   node node-practice/run.js --solutions # checks solutions.js (reference)

const target = process.argv.includes('--solutions')
  ? require('./solutions')
  : require('./exercises');

const cases = [
  { name: 'countUpTo(5)', actual: () => target.countUpTo(5), expected: [1, 2, 3, 4, 5] },
  { name: 'sumUpTo(5)', actual: () => target.sumUpTo(5), expected: 15 },
  { name: 'sumUpTo(100)', actual: () => target.sumUpTo(100), expected: 5050 },
  { name: 'evensUpTo(10)', actual: () => target.evensUpTo(10), expected: [0, 2, 4, 6, 8, 10] },
  {
    name: 'fizzBuzz(15)',
    actual: () => target.fizzBuzz(15),
    expected: [
      '1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz',
      '11', 'Fizz', '13', '14', 'FizzBuzz',
    ],
  },
  { name: 'findMax([3, 7, 2, 9, 4])', actual: () => target.findMax([3, 7, 2, 9, 4]), expected: 9 },
  { name: 'reverseArray([1, 2, 3])', actual: () => target.reverseArray([1, 2, 3]), expected: [3, 2, 1] },
  { name: 'drawSquare(3)', actual: () => target.drawSquare(3), expected: '***\n***\n***' },
];

let passed = 0;

for (const { name, actual, expected } of cases) {
  let result;
  let error;
  try {
    result = actual();
  } catch (err) {
    error = err;
  }

  const ok = !error && JSON.stringify(result) === JSON.stringify(expected);

  if (ok) {
    passed++;
    console.log(`PASS  ${name}`);
  } else if (error) {
    console.log(`FAIL  ${name}  threw: ${error.message}`);
  } else {
    console.log(`FAIL  ${name}`);
    console.log(`      expected: ${JSON.stringify(expected)}`);
    console.log(`      got:      ${JSON.stringify(result)}`);
  }
}

console.log(`\n${passed}/${cases.length} passed`);
