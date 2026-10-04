import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { ExecutionResult, TransactionHash, TransactionHashVariant, TransactionStatus } from 'genlayer-js/types';

type Provider = NonNullable<Window['ethereum']>;

export const CHAIN_ID = 61999;
export const CONTRACT = (import.meta.env.VITE_CONTRACT_ADDRESS || '').trim();
export const configured = /^0x[a-fA-F0-9]{40}$/.test(CONTRACT) && !/^0x0{40}$/.test(CONTRACT);
export const reader = createClient({ chain: studionet });
export const explorerAddress = configured ? `https://explorer-studio.genlayer.com/address/${CONTRACT}` : '';
export const txUrl = (hash: string) => `https://explorer-studio.genlayer.com/tx/${hash}`;

export async function connectWallet(provider: Provider | undefined = window.ethereum) {
  if (!provider?.request) throw new Error('Install or enable an injected wallet such as Rabby or MetaMask.');
  const accounts = await provider.request({ method: 'eth_requestAccounts' }) as string[];
  const account = accounts?.[0] || '';
  if (!/^0x[a-fA-F0-9]{40}$/.test(account)) throw new Error('The wallet returned no valid account.');
  const chain = BigInt(String(await provider.request({ method: 'eth_chainId' })));
  if (chain !== BigInt(CHAIN_ID)) throw new Error('Switch the wallet to GenLayer Studionet (chain ID 61999).');
  return account;
}

export async function connectedClient(expected: string, provider: Provider | undefined = window.ethereum) {
  const account = await connectWallet(provider);
  if (expected && expected.toLowerCase() !== account.toLowerCase()) {
    throw new Error('Wallet account changed. Reconnect before signing.');
  }
  return {
    account,
    client: createClient({ chain: studionet, provider: provider as never, account: account as `0x${string}` }),
  };
}

export async function readFinalized<T = unknown>(functionName: string, args: unknown[] = []) {
  if (!configured) throw new Error('Contract address is not configured.');
  return reader.readContract({
    address: CONTRACT as `0x${string}`,
    functionName,
    args,
    transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
    jsonSafeReturn: true,
  } as never) as Promise<T>;
}

export async function writeFinalized(expectedAccount: string, functionName: string, args: unknown[]) {
  if (!configured) throw new Error('Contract address is not configured.');
  const { client } = await connectedClient(expectedAccount);
  const hash = await client.writeContract({
    address: CONTRACT as `0x${string}`,
    functionName,
    args,
    value: 0n,
  } as never) as string;
  if (!/^0x[a-fA-F0-9]{64}$/.test(hash)) throw new Error('Wallet returned an invalid transaction hash.');
  const receipt = await client.waitForTransactionReceipt({
    hash: hash as TransactionHash,
    status: TransactionStatus.FINALIZED,
  });
  if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) {
    throw new Error(`Transaction finalized with ${receipt.txExecutionResultName || 'no execution result'}.`);
  }
  return hash;
}

export const short = (value: string) => value ? `${value.slice(0, 6)}…${value.slice(-4)}` : 'Not connected';
