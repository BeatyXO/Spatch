import { describe, expect, it } from 'vitest';
import { assertSuccessfulWrite, parsePositiveInt, statusLabel, statusTone } from './actions';

describe('presentation helpers', () => {
  it('formats contract states for humans', () => {
    expect(statusLabel('RECHECK_REQUIRED')).toBe('Recheck Required');
    expect(statusTone('VULNERABLE')).toBe('danger');
    expect(statusTone('ACTIVE')).toBe('success');
    expect(statusTone('SECURITY_REASSESS_REQUIRED')).toBe('warning');
    expect(statusTone('UNRESOLVED')).toBe('warning');
  });

  it('rejects unsafe ids before calldata creation', () => {
    expect(() => parsePositiveInt('0', 'Project ID')).toThrow();
    expect(() => parsePositiveInt('1.2', 'Project ID')).toThrow();
    expect(parsePositiveInt('4', 'Project ID')).toBe(4);
  });

  it('treats finalized contract no-ops as failures', () => {
    expect(() => assertSuccessfulWrite('add_component', 'ONLY_PROJECT_CREATOR')).toThrow(/without changing state/);
    expect(() => assertSuccessfulWrite('assess_advisory', 'ADVISORY_ALREADY_ASSESSED_FOR_CURRENT_REVISIONS')).toThrow();
    expect(() => assertSuccessfulWrite('seal_project', 'SEALED')).not.toThrow();
    expect(() => assertSuccessfulWrite('verify_patch', '7')).not.toThrow();
    expect(() => assertSuccessfulWrite('create_project', 0)).toThrow(/without changing state/);
    expect(() => assertSuccessfulWrite('create_project', undefined)).toThrow(/could not be verified/);
    expect(() => assertSuccessfulWrite('create_project', { status: 'return', payload: { readable: '1' } })).not.toThrow();
    expect(() => assertSuccessfulWrite('seal_project', { status: 'return', payload: { readable: '"SEALED"' } })).not.toThrow();
    expect(() => assertSuccessfulWrite('add_component', { status: 'return', payload: { readable: '"ONLY_PROJECT_CREATOR"' } })).toThrow(/ONLY_PROJECT_CREATOR/);
  });
});
