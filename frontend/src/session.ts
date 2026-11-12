import type { QueryClient } from '@tanstack/react-query';

/** Keep the observed account query alive while discarding all private account data. */
export function discardPrivateQueries(client: QueryClient) {
  const filters = {
    predicate: (query: { queryKey: readonly unknown[] }) => query.queryKey[0] !== 'me',
  };
  void client.cancelQueries();
  client.removeQueries(filters);
}
