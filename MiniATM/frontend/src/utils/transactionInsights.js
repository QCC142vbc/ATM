const asAmount = (transaction) => Number(transaction.amount) || 0

export function getTransactionTotals(transactions) {
  return transactions.reduce((totals, transaction) => {
    totals.count += 1
    if (transaction.transaction_type === 'deposit') totals.deposits += asAmount(transaction)
    if (transaction.transaction_type === 'withdrawal') totals.withdrawals += asAmount(transaction)
    if (transaction.transaction_type === 'transfer_sent') totals.transfersSent += asAmount(transaction)
    if (transaction.transaction_type === 'transfer_received') totals.transfersReceived += asAmount(transaction)
    return totals
  }, { deposits: 0, withdrawals: 0, transfersSent: 0, transfersReceived: 0, count: 0 })
}

export function getMonthlyActivity(transactions, now = new Date()) {
  const buckets = Array.from({ length: 6 }, (_, offset) => {
    const month = new Date(now.getFullYear(), now.getMonth() - 5 + offset, 1)
    return {
      key: `${month.getFullYear()}-${month.getMonth()}`,
      label: month.toLocaleDateString(undefined, { month: 'short' }),
      deposits: 0,
      withdrawals: 0,
      transfers: 0,
      count: 0,
    }
  })
  const byMonth = new Map(buckets.map((bucket) => [bucket.key, bucket]))

  transactions.forEach((transaction) => {
    const date = new Date(transaction.timestamp)
    if (Number.isNaN(date.getTime())) return
    const bucket = byMonth.get(`${date.getFullYear()}-${date.getMonth()}`)
    if (!bucket) return
    bucket.count += 1
    if (transaction.transaction_type === 'deposit') bucket.deposits += asAmount(transaction)
    if (transaction.transaction_type === 'withdrawal') bucket.withdrawals += asAmount(transaction)
    if (transaction.transaction_type.startsWith('transfer_')) bucket.transfers += asAmount(transaction)
  })

  return buckets
}
