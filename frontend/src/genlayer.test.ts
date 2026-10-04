import { describe, expect, it, vi } from 'vitest';
import { CHAIN_ID, switchToStudionet } from './genlayer';

function wallet(responses: Record<string, unknown | Error>) {
  const request = vi.fn(async ({ method }: { method: string }) => {
    const result = responses[method];
    if (result instanceof Error) throw result;
    return result;
  });
  return { request } as never as NonNullable<Window['ethereum']> & { request: typeof request };
}

describe('Studionet wallet switching', () => {
  it('switches to chain 61999 when it is already configured', async () => {
    const provider = wallet({ wallet_switchEthereumChain: null, eth_chainId: '0xf22f' });
    await switchToStudionet(provider);
    expect(provider.request).toHaveBeenCalledWith({ method: 'wallet_switchEthereumChain', params: [{ chainId: '0xf22f' }] });
  });

  it('adds the official Studionet RPC and retries switching when the wallet does not know it', async () => {
    const provider = wallet({
      wallet_switchEthereumChain: Object.assign(new Error('Unrecognized chain'), { code: 4902 }),
      wallet_addEthereumChain: null,
      eth_chainId: '0xf22f',
    });
    provider.request.mockImplementation(async ({ method }: { method: string }) => {
      if (method === 'wallet_switchEthereumChain' && provider.request.mock.calls.filter(([call]) => call.method === method).length === 1) {
        throw Object.assign(new Error('Unrecognized chain'), { code: 4902 });
      }
      if (method === 'eth_chainId') return `0x${CHAIN_ID.toString(16)}`;
      return null;
    });

    await switchToStudionet(provider);
    expect(provider.request).toHaveBeenCalledWith({
      method: 'wallet_addEthereumChain',
      params: [{
        chainId: '0xf22f',
        chainName: 'GenLayer Studionet',
        nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
        rpcUrls: ['https://studio.genlayer.com/api'],
        blockExplorerUrls: ['https://explorer-studio.genlayer.com'],
      }],
    });
    expect(provider.request.mock.calls.filter(([call]) => call.method === 'wallet_switchEthereumChain')).toHaveLength(2);
  });

  it('does not add or switch chains after the user rejects a switch request', async () => {
    const rejected = Object.assign(new Error('User rejected request'), { code: 4001 });
    const provider = wallet({ wallet_switchEthereumChain: rejected });
    await expect(switchToStudionet(provider)).rejects.toBe(rejected);
    expect(provider.request).toHaveBeenCalledTimes(1);
  });
});
