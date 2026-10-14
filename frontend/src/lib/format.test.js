import { test } from 'node:test';
import assert from 'node:assert/strict';
import { greeting, initials, nextHalfHourInput, nextStatus, statusLabel } from './format.js';
import { describeError } from './api.js';

test('statusLabel humanises enum values', () => {
  assert.equal(statusLabel('CHECKED_IN'), 'Checked In');
  assert.equal(statusLabel('SCHEDULED'), 'Scheduled');
});

test('nextStatus walks the appointment lifecycle', () => {
  assert.equal(nextStatus('SCHEDULED'), 'CHECKED_IN');
  assert.equal(nextStatus('CHECKED_IN'), 'COMPLETED');
  assert.equal(nextStatus('COMPLETED'), null);
  assert.equal(nextStatus('CANCELLED'), null);
});

test('initials ignores the Dr. prefix', () => {
  assert.equal(initials('Dr. Ananya Mehta'), 'AM');
  assert.equal(initials('Priya'), 'P');
});

test('nextHalfHourInput rounds up to the next slot', () => {
  assert.equal(nextHalfHourInput(new Date(2030, 0, 15, 9, 10)), '2030-01-15T09:30');
  assert.equal(nextHalfHourInput(new Date(2030, 0, 15, 9, 45)), '2030-01-15T10:00');
});

test('greeting follows the clock', () => {
  assert.equal(greeting(new Date(2030, 0, 1, 8)), 'Good morning');
  assert.equal(greeting(new Date(2030, 0, 1, 20)), 'Good evening');
});

test('describeError flattens FastAPI validation errors', () => {
  assert.equal(describeError({ detail: 'Doctor not found' }), 'Doctor not found');
  assert.equal(
    describeError({ detail: [{ loc: ['body', 'patient_phone'], msg: 'invalid' }] }),
    'patient_phone: invalid',
  );
});
