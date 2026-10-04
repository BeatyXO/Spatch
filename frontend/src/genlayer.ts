import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { ExecutionResult, TransactionHash, TransactionHashVariant, TransactionStatus } from 'genlayer-js/types';
import { assertSuccessfulWrite } from './actions';

type Provider = NonNullable<Window['ethereum']> & {
  on?: (event: string, listener: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, listener: (...args: unknown[]) => void) => void;
};

export const CHAIN_ID = 61999;
const CHAIN_ID_HEX = `0x${CHAIN_ID.toString(16)}`;
const STUDIONET_CHAIN = {
  chainId: CHAIN_ID_HEX,
  chainName: 'GenLayer Studionet',
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  rpcUrls: ['https://studio.genlayer.com/api'],
  blockExplorerUrls: ['https://explorer-studio.genlayer.com'],
};
export const CONTRACT = (import.meta.env.VITE_CONTRACT_ADDRESS || '').trim();
export const configured = /^0x[a-fA-F0-9]{40}$/.test(CONTRACT) && !/^0x0{40}$/.test(CONTRACT);
export const reader = createClient({ chain: studionet });
export const explorerAddress = configured ? `https://explorer-studio.genlayer.com/address/${CONTRACT}` : '';
export const txUrl = (hash: string) => `https://explorer-studio.genlayer.com/tx/${hash}`;

export class FinalizedWriteError extends Error {
  constructor(message: string, readonly txHash: string) {
    super(message);
    this.name = 'FinalizedWriteError';
  }
}

export async function connectWallet(provider: Provider | undefined = window.ethereum) {
  if (!provider?.request) throw new Error('Install or enable an injected wallet such as Rabby or MetaMask.');
  const accounts = await provider.request({ method: 'eth_requestAccounts' }) as string[];
  const account = accounts?.[0] || '';
  if (!/^0x[a-fA-F0-9]{40}$/.test(account)) throw new Error('The wallet returned no valid account.');
  const chain = BigInt(String(await provider.request({ method: 'eth_chainId' })));
  if (chain !== BigInt(CHAIN_ID)) throw new Error('Your wallet is on the wrong network. Choose “Switch to Studionet” in the wallet menu.');
  return account;
}

export async function switchToStudionet(provider: Provider | undefined = window.ethereum) {
  if (!provider?.request) throw new Error('Install or enable an injected wallet such as Rabby or MetaMask.');
  try {
    await provider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: CHAIN_ID_HEX }] });
  } catch (error) {
    const code = (error as { code?: number })?.code;
    if (code !== 4902) throw error;
    await provider.request({ method: 'wallet_addEthereumChain', params: [STUDIONET_CHAIN] });
    await provider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: CHAIN_ID_HEX }] });
  }
  const chain = BigInt(String(await provider.request({ method: 'eth_chainId' })));
  if (chain !== BigInt(CHAIN_ID)) throw new Error('The wallet did not switch to GenLayer Studionet (chain ID 61999).');
}

export async function disconnectWallet(provider: Provider | undefined = window.ethereum) {
  if (!provider?.request) return;
  // Revoke account access where the injected wallet implements the optional method.
  try { await provider.request({ method: 'wallet_revokePermissions', params: [{ eth_accounts: {} }] }); }
  catch { /* The app still clears its local connection when a wallet lacks revocation support. */ }
}

export async function walletState(provider: Provider | undefined = window.ethereum) {
  if (!provider?.request) return { account: '', wrongNetwork: false };
  const [accounts, chainId] = await Promise.all([
    provider.request({ method: 'eth_accounts' }) as Promise<string[]>,
    provider.request({ method: 'eth_chainId' }) as Promise<string>,
  ]);
  const account = accounts?.[0] || '';
  return {
    account: /^0x[a-fA-F0-9]{40}$/.test(account) ? account : '',
    wrongNetwork: BigInt(String(chainId)) !== BigInt(CHAIN_ID),
  };
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
  } as never) as Awaited<ReturnType<typeof client.waitForTransactionReceipt>> & {
    consensus_data?: { leader_receipt?: Array<{ mode?: string; result?: unknown }> };
  };
  if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) {
    throw new FinalizedWriteError(`Transaction finalized with ${receipt.txExecutionResultName || 'no execution result'}.`, hash);
  }
  const leaderReceipt = receipt.consensus_data?.leader_receipt?.find((entry) => entry.mode === 'leader');
  if (!leaderReceipt) {
    throw new FinalizedWriteError('Transaction finalized, but its leader return value is missing; verify finalized contract state before assuming success.', hash);
  }
  try { assertSuccessfulWrite(functionName, leaderReceipt.result); }
  catch (error) {
    throw new FinalizedWriteError(error instanceof Error ? error.message : String(error), hash);
  }
  return hash;
}

export const short = (value: string) => value ? `${value.slice(0, 6)}…${value.slice(-4)}` : 'Not connected';
