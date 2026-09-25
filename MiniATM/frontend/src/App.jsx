import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  ArrowDownLeft,
  ArrowRightLeft,
  ArrowUpRight,
  Banknote,
  BarChart3,
  Check,
  ChevronRight,
  Eye,
  EyeOff,
  FileText,
  Landmark,
  LogOut,
  Menu,
  Search,
  Send,
  Settings,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  UserRound,
  Wallet,
  X,
} from 'lucide-react'
import { api } from './services/api'
import { getMonthlyActivity, getTransactionTotals } from './utils/transactionInsights'
import './App.css'

const quickAmounts = [20, 50, 100, 200]
const transactionFilters = [
  { key: 'all', label: 'All' },
  { key: 'deposit', label: 'Deposits' },
  { key: 'withdrawal', label: 'Withdrawals' },
  { key: 'transfer', label: 'Transfers' },
]
const navigation = [
  { key: 'dashboard', label: 'Overview', icon: Wallet },
  { key: 'transactions', label: 'Transactions', icon: ArrowRightLeft },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
  { key: 'account', label: 'Profile & settings', icon: Settings },
]

const formatCurrency = (value) => new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(Number(value) || 0)

const formatTransactionType = (type) => ({
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  transfer_sent: 'Transfer sent',
  transfer_received: 'Transfer received',
}[type] || type)

const isCredit = (transaction) => (
  transaction.transaction_type === 'deposit' || transaction.transaction_type === 'transfer_received'
)

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

const errorCode = (error) => error?.payload?.error?.code

function TransactionIcon({ type }) {
  if (type === 'deposit') return <TrendingUp size={16} />
  if (type === 'withdrawal') return <TrendingDown size={16} />
  return <ArrowRightLeft size={16} />
}

function TransactionRow({ transaction, onSelect }) {
  const credit = isCredit(transaction)

  return (
    <button className="transaction-item transaction-selectable" onClick={() => onSelect(transaction)}>
      <div className="transaction-icon"><TransactionIcon type={transaction.transaction_type} /></div>
      <div className="transaction-copy">
        <strong>{formatTransactionType(transaction.transaction_type)}</strong>
        <span>
          {transaction.counterparty_name
            ? `${credit ? 'From' : 'To'} ${transaction.counterparty_name} · `
            : ''}
          {new Date(transaction.timestamp).toLocaleString()}
        </span>
      </div>
      <div className="transaction-meta">
        <div className={`transaction-amount ${credit ? 'positive' : 'negative'}`}>
          {credit ? '+' : '-'}{formatCurrency(transaction.amount)}
        </div>
        <small>Balance {formatCurrency(transaction.balance_after)}</small>
      </div>
      <ChevronRight className="transaction-chevron" size={16} />
    </button>
  )
}

function UsageBar({ label, used, limit }) {
  const usedAmount = Number(used) || 0
  const limitAmount = Number(limit) || 0
  const percentage = limitAmount > 0 ? Math.min(100, (usedAmount / limitAmount) * 100) : 0
  return (
    <div className="usage-card">
      <div className="usage-copy">
        <span>{label}</span>
        <strong>{formatCurrency(usedAmount)} / {formatCurrency(limitAmount)}</strong>
      </div>
      <div className="usage-track" role="progressbar" aria-label={label} aria-valuenow={Math.round(percentage)} aria-valuemax="100">
        <span style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

function App() {
  const [user, setUser] = useState(null)
  const [account, setAccount] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [error, setError] = useState('')
  const [remainingAttempts, setRemainingAttempts] = useState(3)
  const [showPin, setShowPin] = useState(false)
  const [showBalance, setShowBalance] = useState(true)
  const [transactionModal, setTransactionModal] = useState(null)
  const [transactionAmount, setTransactionAmount] = useState('')
  const [transactionLoading, setTransactionLoading] = useState(false)
  const [transactionFeedback, setTransactionFeedback] = useState('')
  const [transferStage, setTransferStage] = useState('input')
  const [transferDraft, setTransferDraft] = useState(null)
  const [transferError, setTransferError] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [mobileHistoryFilter, setMobileHistoryFilter] = useState('all')
  const [transactionSearch, setTransactionSearch] = useState('')
  const [historySort, setHistorySort] = useState('newest')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [amountFrom, setAmountFrom] = useState('')
  const [amountTo, setAmountTo] = useState('')
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [toast, setToast] = useState(null)
  const [atmMode, setAtmMode] = useState(false)
  const [atmCash, setAtmCash] = useState(null)
  const [atmCashError, setAtmCashError] = useState('')
  const toastTimeout = useRef(null)

  const showToast = useCallback((message, kind = 'success') => {
    setToast({ message, kind, id: Date.now() })
    if (toastTimeout.current) window.clearTimeout(toastTimeout.current)
    toastTimeout.current = window.setTimeout(() => setToast(null), 4200)
  }, [])

  const handleSessionFailure = useCallback((failure) => {
    if (!['UNAUTHORIZED', 'SESSION_EXPIRED', 'ACCOUNT_UNAVAILABLE'].includes(errorCode(failure))) {
      return false
    }
    setUser(null)
    setAccount(null)
    setTransactions([])
    setTransactionModal(null)
    setAtmMode(false)
    setError('Your session has expired. Please sign in again.')
    showToast('Your session has expired. Please sign in again.', 'error')
    return true
  }, [showToast])

  const loadDashboard = useCallback(async () => {
    try {
      const [accountData, transactionsData] = await Promise.all([
        api.getAccount(),
        api.getTransactions(),
      ])
      setAccount(accountData)
      setTransactions(transactionsData)
      return true
    } catch (loadError) {
      if (!handleSessionFailure(loadError)) {
        showToast(loadError.message || 'Unable to load account data.', 'error')
      }
      return false
    }
  }, [handleSessionFailure, showToast])

  useEffect(() => {
    let mounted = true
    const bootstrap = async () => {
      try {
        const session = await api.session()
        if (!mounted) return
        setUser({ user_id: session.user_id, name: session.name })
        await loadDashboard()
      } catch (bootstrapError) {
        if (mounted) handleSessionFailure(bootstrapError)
      } finally {
        if (mounted) setPageLoading(false)
      }
    }
    bootstrap()
    return () => {
      mounted = false
      if (toastTimeout.current) window.clearTimeout(toastTimeout.current)
    }
  }, [handleSessionFailure, loadDashboard])

  useEffect(() => {
    if (!atmMode || !user) return
    api.getAtmCash()
      .then(setAtmCash)
      .catch((cashError) => {
        if (!handleSessionFailure(cashError)) {
          setAtmCashError(cashError.message || 'ATM cash inventory is unavailable.')
        }
      })
  }, [atmMode, handleSessionFailure, user])

  const totals = useMemo(() => getTransactionTotals(transactions), [transactions])
  const monthlyActivity = useMemo(() => getMonthlyActivity(transactions), [transactions])
  const maxActivity = Math.max(
    1,
    ...monthlyActivity.flatMap(({ deposits, withdrawals, transfers }) => [deposits, withdrawals, transfers]),
  )

  const filteredTransactions = useMemo(() => {
    const query = transactionSearch.trim().toLowerCase()
    return transactions.filter((transaction) => {
      const type = transaction.transaction_type
      if (mobileHistoryFilter === 'deposit' && type !== 'deposit') return false
      if (mobileHistoryFilter === 'withdrawal' && type !== 'withdrawal') return false
      if (mobileHistoryFilter === 'transfer' && !type.startsWith('transfer_')) return false
      const searchableText = [
        transaction.transaction_id,
        transaction.transfer_id,
        transaction.description,
        transaction.counterparty_id,
        transaction.counterparty_name,
        transaction.transaction_type,
        transaction.amount,
      ].filter(Boolean).join(' ').toLowerCase()
      if (query && !searchableText.includes(query)) return false
      const date = new Date(transaction.timestamp)
      if (dateFrom && date < new Date(`${dateFrom}T00:00:00`)) return false
      if (dateTo && date > new Date(`${dateTo}T23:59:59.999`)) return false
      const amount = Number(transaction.amount)
      if (amountFrom !== '' && amount < Number(amountFrom)) return false
      if (amountTo !== '' && amount > Number(amountTo)) return false
      return true
    }).sort((left, right) => {
      const dateDifference = new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime()
      return historySort === 'oldest' ? dateDifference : -dateDifference
    })
  }, [transactions, mobileHistoryFilter, transactionSearch, dateFrom, dateTo, amountFrom, amountTo, historySort])

  const handleLogin = async (event) => {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    const userId = String(values.get('user_id') || '').trim()
    const pin = String(values.get('pin') || '')
    setLoading(true)
    setError('')

    try {
      const response = await api.login(userId, pin)
      const nextUser = response.user ?? response
      setUser({ user_id: nextUser.user_id || nextUser.userId, name: nextUser.name })
      form.reset()
      const loaded = await loadDashboard()
      if (loaded) {
        setRemainingAttempts(3)
        setActiveTab('dashboard')
        showToast(`Welcome, ${nextUser.name}.`)
      }
    } catch (loginError) {
      const payloadError = loginError.payload?.error
      setError(payloadError?.message || loginError.message || 'Login failed.')
      setRemainingAttempts(payloadError?.remaining_attempts ?? remainingAttempts)
      if (payloadError?.remaining_attempts === 0 || payloadError?.code === 'MAX_ATTEMPTS_REACHED') {
        setRemainingAttempts(0)
      }
      showToast(payloadError?.message || 'Unable to sign in.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await api.logout()
    } catch (logoutError) {
      showToast(logoutError.message || 'Could not reach the server to sign out.', 'error')
      return
    }
    setUser(null)
    setAccount(null)
    setTransactions([])
    setTransactionModal(null)
    setTransactionAmount('')
    setTransactionFeedback('')
    setRemainingAttempts(3)
    setError('')
    setAtmMode(false)
    showToast('You have been signed out.')
  }

  const openTransaction = (type) => {
    setTransactionModal(type)
    setTransactionAmount('')
    setTransactionFeedback('')
    setTransferStage('input')
    setTransferDraft(null)
    setTransferError('')
  }

  const closeTransaction = () => {
    if (transactionLoading) return
    setTransactionModal(null)
    setTransactionAmount('')
    setTransactionFeedback('')
    setTransferDraft(null)
    setTransferError('')
  }

  const submitTransaction = async (type) => {
    const amount = Number(transactionAmount)
    if (!Number.isFinite(amount) || amount <= 10) {
      setTransactionFeedback('Enter an amount greater than €10.00.')
      return
    }

    setTransactionLoading(true)
    setTransactionFeedback('')
    try {
      const result = type === 'deposit'
        ? await api.deposit(amount)
        : atmMode
          ? await api.atmWithdraw(amount)
          : await api.withdraw(amount)
      await loadDashboard()
      setAccount((current) => ({ ...current, balance: result?.balance ?? current?.balance }))
      setTransactionModal(null)
      setTransactionAmount('')
      setTransactionFeedback('')
      if (type === 'deposit') {
        showToast(`Deposit of ${formatCurrency(amount)} completed.`)
      } else if (result?.banknotes) {
        const dispensed = Object.entries(result.banknotes)
          .map(([denomination, count]) => `${count} × €${denomination}`)
          .join(', ')
        showToast(`ATM withdrawal complete. Dispensed: ${dispensed || 'cash'}.`)
        setAtmCash((current) => current
          ? { ...current, total_cash: result.total_cash }
          : current)
      } else {
        showToast(`Withdrawal of ${formatCurrency(amount)} completed.`)
      }
    } catch (transactionError) {
      if (!handleSessionFailure(transactionError)) {
        setTransactionFeedback(transactionError.message || 'Transaction failed.')
        showToast(transactionError.message || 'Transaction failed.', 'error')
      }
    } finally {
      setTransactionLoading(false)
    }
  }

  const prepareTransfer = (event) => {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const recipientId = String(values.get('recipient_id') || '').trim()
    const description = String(values.get('description') || '').trim()
    const amount = Number(values.get('amount'))
    if (!recipientId || recipientId === user.user_id) {
      setTransferError(recipientId === user.user_id
        ? 'Choose a different recipient account.'
        : 'Enter the recipient user ID.')
      return
    }
    if (!Number.isFinite(amount) || amount <= 10) {
      setTransferError('Enter an amount greater than €10.00.')
      return
    }
    setTransferDraft({ recipientId, description, amount })
    setTransferError('')
    setTransferStage('confirm')
  }

  const confirmTransfer = async () => {
    if (!transferDraft) return
    setTransactionLoading(true)
    setTransferError('')
    try {
      await api.transfer(transferDraft)
      await loadDashboard()
      setTransferStage('success')
      showToast(`Transfer of ${formatCurrency(transferDraft.amount)} completed.`)
    } catch (transferFailure) {
      if (!handleSessionFailure(transferFailure)) {
        setTransferError(transferFailure.message || 'Transfer failed.')
        showToast(transferFailure.message || 'Transfer failed.', 'error')
      }
    } finally {
      setTransactionLoading(false)
    }
  }

  const handleChangePin = async (event) => {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    setLoading(true)
    try {
      await api.changePin({
        currentPin: String(values.get('current_pin') || ''),
        newPin: String(values.get('new_pin') || ''),
        confirmPin: String(values.get('confirm_pin') || ''),
      })
      form.reset()
      showToast('Your PIN was changed successfully.')
    } catch (pinError) {
      if (!handleSessionFailure(pinError)) {
        showToast(pinError.message || 'Could not change your PIN.', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const selectTab = (key) => {
    setActiveTab(key)
    setMobileMenuOpen(false)
    setAtmMode(false)
  }

  if (pageLoading) {
    return <div className="loading-screen"><div className="loading-spinner" /></div>
  }

  if (!user) {
    return (
      <div className="login-page">
        {toast && <div className={`toast ${toast.kind}`} role="status">{toast.message}</div>}
        <div className="login-card">
          <div className="brand-block">
            <div className="brand-mark"><Landmark size={28} /></div>
            <div>
              <p className="eyebrow">MiniATM v2</p>
              <h1>Banking, made clear.</h1>
            </div>
          </div>
          <p className="login-intro">Secure access to your account, activity, and everyday banking tools.</p>
          <form onSubmit={handleLogin} className="login-form">
            <label>
              <span>User ID</span>
              <input type="text" name="user_id" autoComplete="username" placeholder="Your user ID" required />
            </label>
            <label>
              <span>PIN</span>
              <div className="password-wrap">
                <input
                  type={showPin ? 'text' : 'password'}
                  name="pin"
                  autoComplete="current-password"
                  inputMode="numeric"
                  pattern="[0-9]{4,12}"
                  maxLength={12}
                  placeholder="Enter your PIN"
                  required
                />
                <button type="button" className="icon-button" aria-label={showPin ? 'Hide PIN' : 'Show PIN'} onClick={() => setShowPin((current) => !current)}>
                  {showPin ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>
            {error && <div className="form-message error">{error}</div>}
            {remainingAttempts > 0 && remainingAttempts < 3 && (
              <div className="form-message muted">{remainingAttempts} attempt{remainingAttempts === 1 ? '' : 's'} remaining.</div>
            )}
            {remainingAttempts === 0 && <div className="form-message error">Maximum login attempts reached.</div>}
            <button type="submit" className="primary-button" disabled={loading || remainingAttempts === 0}>
              {loading ? 'Signing in...' : 'Sign in securely'}
            </button>
          </form>
          <div className="login-security"><ShieldCheck size={16} /> Your PIN is never shown or saved by this interface.</div>
        </div>
      </div>
    )
  }

  const recentTransactions = [...transactions]
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
    .slice(0, 4)

  return (
    <div className={`app-shell ${atmMode ? 'atm-app-shell' : ''}`}>
      {!atmMode && (
        <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`}>
          <div className="brand-inline">
            <div className="brand-mark small"><Landmark size={22} /></div>
            <div><p className="eyebrow">MiniATM v2</p><h2>Banking</h2></div>
          </div>
          <nav className="nav-pills">
            {navigation.map(({ key, label, icon: Icon }) => (
              <button key={key} className={activeTab === key ? 'nav-item active' : 'nav-item'} onClick={() => selectTab(key)}>
                <Icon size={18} />{label}
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-status"><span className="status-dot" /> Account {account?.status?.toLowerCase() || 'active'}</div>
            <button className="logout-button" onClick={handleLogout}><LogOut size={18} />Sign out</button>
          </div>
        </aside>
      )}

      <main className="main-panel">
        <header className="topbar">
          {!atmMode && (
            <div className="mobile-toggle-wrap">
              <button className="mobile-menu-button" aria-label="Toggle menu" onClick={() => setMobileMenuOpen((current) => !current)}>
                <Menu size={20} />
              </button>
            </div>
          )}
          <div className="mode-switch" role="group" aria-label="Interface mode">
            <button className={!atmMode ? 'selected' : ''} onClick={() => setAtmMode(false)}>Banking</button>
            <button className={atmMode ? 'selected' : ''} onClick={() => setAtmMode(true)}>ATM mode</button>
          </div>
          <div className="user-badge">
            <div className="avatar">{user.name?.charAt(0)?.toUpperCase() || 'U'}</div>
            <div><span className="label">Signed in</span><strong>{user.name}</strong></div>
          </div>
        </header>

        {atmMode ? (
          <section className="atm-shell" aria-label="ATM mode">
            <div className="atm-screen">
              <div className="atm-brand"><Landmark size={22} /><span>MiniATM <small>SELF-SERVICE</small></span></div>
              <p className="eyebrow">Welcome back</p>
              <h2>{user.name}</h2>
              <p className="atm-balance-label">Available balance</p>
              <div className="atm-balance">{showBalance ? formatCurrency(account?.balance) : '••••••'}</div>
              <button className="atm-reveal" onClick={() => setShowBalance((current) => !current)}>
                {showBalance ? <EyeOff size={15} /> : <Eye size={15} />}
                {showBalance ? 'Hide balance' : 'Show balance'}
              </button>
              <div className="atm-cash-line">
                <Banknote size={16} />
                <span>Cash available in this ATM</span>
                <strong>{atmCash ? formatCurrency(atmCash.total_cash) : 'Loading…'}</strong>
              </div>
              {atmCashError && <div className="form-message error">{atmCashError}</div>}
              <div className="atm-actions">
                <button onClick={() => openTransaction('withdraw')}><ArrowUpRight size={19} />Withdraw cash</button>
                <button onClick={() => openTransaction('deposit')}><ArrowDownLeft size={19} />Deposit funds</button>
                <button onClick={() => openTransaction('transfer')}><Send size={19} />Transfer money</button>
                <button onClick={() => selectTab('transactions')}><FileText size={19} />Transaction history</button>
              </div>
              <div className="atm-footnote"><ShieldCheck size={15} /> Authenticated session · {user.user_id}</div>
            </div>
            <button className="atm-logout" onClick={handleLogout}><LogOut size={17} />End session</button>
          </section>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <section className="content-section">
                <div className="section-header">
                  <div><p className="eyebrow primary">{getGreeting()}, {user.name}</p><h3>Your money, at a glance.</h3></div>
                  <div className="status-badge"><span className="status-dot" />{account?.status || 'ACTIVE'}</div>
                </div>
                <div className="balance-card">
                  <div className="balance-topline">
                    <span>Available balance</span>
                    <button className="ghost-button" aria-label={showBalance ? 'Hide balance' : 'Show balance'} onClick={() => setShowBalance((current) => !current)}>
                      {showBalance ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <div className="balance-value">{showBalance ? formatCurrency(account?.balance) : '••••••'}</div>
                  <div className="account-meta">
                    <div><span>Account</span><strong>{account?.user_id || user.user_id}</strong></div>
                    <div><span>Account holder</span><strong>{user.name}</strong></div>
                    <div><span>Account status</span><strong>{account?.status || 'ACTIVE'}</strong></div>
                  </div>
                </div>
                <div className="quick-actions">
                  <button className="action-button deposit" onClick={() => openTransaction('deposit')}><TrendingUp size={18} />Deposit</button>
                  <button className="action-button withdraw" onClick={() => openTransaction('withdraw')}><TrendingDown size={18} />Withdraw</button>
                  <button className="action-button transfer" onClick={() => openTransaction('transfer')}><Send size={18} />Transfer</button>
                  <button className="action-button history-action" onClick={() => selectTab('transactions')}><FileText size={18} />Transactions</button>
                </div>
                <div className="metric-grid">
                  <div className="metric-card"><span>Total deposits</span><strong>{formatCurrency(totals.deposits)}</strong><small>Across {totals.count} recorded transactions</small></div>
                  <div className="metric-card"><span>Total withdrawals</span><strong>{formatCurrency(totals.withdrawals)}</strong><small>Completed account withdrawals</small></div>
                  <div className="metric-card"><span>Transfers sent</span><strong>{formatCurrency(totals.transfersSent)}</strong><small>{formatCurrency(totals.transfersReceived)} received</small></div>
                  <div className="metric-card"><span>Transactions</span><strong>{totals.count}</strong><small>{transactions[0] ? `Latest: ${formatTransactionType(transactions[0].transaction_type)}` : 'No activity yet'}</small></div>
                </div>
                <div className="usage-grid">
                  <UsageBar label="Daily withdrawal usage" used={account?.limits?.withdrawal_used} limit={account?.limits?.withdrawal_limit} />
                  <UsageBar label="Daily transfer usage" used={account?.limits?.transfer_used} limit={account?.limits?.transfer_limit} />
                </div>
                <div className="transactions-panel">
                  <div className="panel-header"><h4>Recent transactions</h4><button className="text-button" onClick={() => selectTab('transactions')}>View all</button></div>
                  <div className="transaction-list">
                    {recentTransactions.length
                      ? recentTransactions.map((transaction) => <TransactionRow key={transaction.transaction_id} transaction={transaction} onSelect={setSelectedTransaction} />)
                      : <p className="empty-state">Your completed activity will appear here.</p>}
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'transactions' && (
              <section className="content-section">
                <div className="section-header">
                  <div><p className="eyebrow primary">Account activity</p><h3>Transaction history</h3></div>
                  <span className="result-count">{filteredTransactions.length} result{filteredTransactions.length === 1 ? '' : 's'}</span>
                </div>
                <div className="transactions-panel full-width">
                  <div className="filter-tabs">
                    {transactionFilters.map(({ key, label }) => (
                      <button key={key} className={mobileHistoryFilter === key ? 'filter-tab active' : 'filter-tab'} onClick={() => setMobileHistoryFilter(key)}>{label}</button>
                    ))}
                  </div>
                  <div className="history-filters">
                    <label className="search-control"><Search size={17} /><input value={transactionSearch} onChange={(event) => setTransactionSearch(event.target.value)} placeholder="Search ID, person, description, amount" /></label>
                    <label><span>Sort by date</span><select value={historySort} onChange={(event) => setHistorySort(event.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></label>
                    <label><span>From</span><input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label>
                    <label><span>To</span><input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label>
                    <label><span>Min amount</span><input type="number" min="0" step="0.01" value={amountFrom} onChange={(event) => setAmountFrom(event.target.value)} placeholder="€0" /></label>
                    <label><span>Max amount</span><input type="number" min="0" step="0.01" value={amountTo} onChange={(event) => setAmountTo(event.target.value)} placeholder="Any" /></label>
                  </div>
                  <div className="transaction-list padded">
                    {filteredTransactions.length
                      ? filteredTransactions.map((transaction) => <TransactionRow key={transaction.transaction_id} transaction={transaction} onSelect={setSelectedTransaction} />)
                      : <p className="empty-state">No transactions match these filters.</p>}
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'analytics' && (
              <section className="content-section">
                <div className="section-header"><div><p className="eyebrow primary">Your activity</p><h3>Financial analytics</h3></div></div>
                <div className="analytics-summary">
                  <div className="metric-card"><span>Recorded transactions</span><strong>{totals.count}</strong><small>Based on your ledger records</small></div>
                  <div className="metric-card"><span>Total deposits</span><strong>{formatCurrency(totals.deposits)}</strong><small>Deposit activity</small></div>
                  <div className="metric-card"><span>Total withdrawals</span><strong>{formatCurrency(totals.withdrawals)}</strong><small>Withdrawal activity</small></div>
                  <div className="metric-card"><span>Transfer activity</span><strong>{formatCurrency(totals.transfersSent + totals.transfersReceived)}</strong><small>Sent and received</small></div>
                </div>
                <div className="transactions-panel analytics-panel">
                  <div className="panel-header"><h4>Monthly activity</h4><span className="muted-copy">Last six months · actual transactions</span></div>
                  <div className="chart-legend">
                    <span><i className="legend-dot deposits" />Deposits</span>
                    <span><i className="legend-dot withdrawals" />Withdrawals</span>
                    <span><i className="legend-dot transfers" />Transfers</span>
                  </div>
                  <div className="monthly-chart">
                    {monthlyActivity.map((month) => (
                      <div className="month-column" key={month.key}>
                        <div className="month-bars">
                          {[['deposits', 'deposits'], ['withdrawals', 'withdrawals'], ['transfers', 'transfers']].map(([key, className]) => (
                            <span key={key} className={`chart-bar ${className}`} title={`${key}: ${formatCurrency(month[key])}`} style={{ height: `${Math.max(month[key] ? 4 : 0, (month[key] / maxActivity) * 100)}%` }} />
                          ))}
                        </div>
                        <span className="month-label">{month.label}</span>
                        <small>{month.count} tx</small>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="transactions-panel">
                  <div className="panel-header"><h4>Account usage limits</h4><Activity size={17} /></div>
                  <div className="usage-grid">
                    <UsageBar label="Daily withdrawal usage" used={account?.limits?.withdrawal_used} limit={account?.limits?.withdrawal_limit} />
                    <UsageBar label="Daily transfer usage" used={account?.limits?.transfer_used} limit={account?.limits?.transfer_limit} />
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'account' && (
              <section className="content-section">
                <div className="section-header"><div><p className="eyebrow primary">Personal details</p><h3>Profile & settings</h3></div></div>
                <div className="account-details-card profile-card">
                  <div className="profile-heading"><div className="profile-avatar"><UserRound size={22} /></div><div><span className="eyebrow primary">Account profile</span><h4>{user.name}</h4></div></div>
                  <div className="detail-row"><span>Account holder</span><strong>{user.name}</strong></div>
                  <div className="detail-row"><span>User ID</span><strong>{account?.user_id || user.user_id}</strong></div>
                  <div className="detail-row"><span>Account status</span><strong className="secure-pill"><ShieldCheck size={14} />{account?.status || 'ACTIVE'}</strong></div>
                  <div className="detail-row"><span>Current balance</span><strong>{showBalance ? formatCurrency(account?.balance) : '••••••'}</strong></div>
                  <div className="detail-row"><span>Total transactions</span><strong>{account?.transaction_count ?? transactions.length}</strong></div>
                  <div className="detail-row"><span>Max withdrawal per transaction</span><strong>{formatCurrency(account?.limits?.max_withdrawal)}</strong></div>
                  <div className="detail-row"><span>Daily withdrawal limit</span><strong>{formatCurrency(account?.limits?.withdrawal_limit)}</strong></div>
                  <div className="detail-row"><span>Max transfer per transaction</span><strong>{formatCurrency(account?.limits?.max_transfer)}</strong></div>
                  <div className="detail-row"><span>Daily transfer limit</span><strong>{formatCurrency(account?.limits?.transfer_limit)}</strong></div>
                </div>
                <div className="account-details-card pin-card">
                  <div className="panel-header"><div><p className="eyebrow primary">Security</p><h4>Change your PIN</h4></div><ShieldCheck size={20} /></div>
                  <p className="settings-description">Choose a new numeric PIN between 4 and 12 digits. Your existing PIN is never displayed.</p>
                  <form className="pin-form" onSubmit={handleChangePin}>
                    <label><span>Current PIN</span><input type="password" name="current_pin" autoComplete="current-password" inputMode="numeric" pattern="[0-9]{4,12}" maxLength={12} required /></label>
                    <label><span>New PIN</span><input type="password" name="new_pin" autoComplete="new-password" inputMode="numeric" pattern="[0-9]{4,12}" maxLength={12} required /></label>
                    <label><span>Confirm new PIN</span><input type="password" name="confirm_pin" autoComplete="new-password" inputMode="numeric" pattern="[0-9]{4,12}" maxLength={12} required /></label>
                    <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Updating…' : 'Update PIN'}</button>
                  </form>
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {transactionModal && (
        <div className="modal-overlay" onMouseDown={(event) => event.target === event.currentTarget && closeTransaction()}>
          <div className="transaction-modal" role="dialog" aria-modal="true" aria-labelledby="transaction-title">
            <div className="modal-header">
              <div>
                <p className="eyebrow primary">{transactionModal === 'transfer' ? 'Between accounts' : atmMode ? 'ATM transaction' : 'Account transaction'}</p>
                <h3 id="transaction-title">
                  {transactionModal === 'transfer' ? 'Transfer money' : transactionModal === 'deposit' ? 'Deposit funds' : 'Withdraw funds'}
                </h3>
              </div>
              <button className="close-button" aria-label="Close dialog" onClick={closeTransaction}><X size={18} /></button>
            </div>

            {transactionModal === 'transfer' ? (
              transferStage === 'input' ? (
                <form className="modal-body" onSubmit={prepareTransfer}>
                  <label className="amount-field"><span>Recipient user ID</span><input name="recipient_id" placeholder="e.g. user002" maxLength={64} required /></label>
                  <label className="amount-field"><span>Amount</span><div className="currency-input"><span>€</span><input name="amount" type="number" min="10.01" step="0.01" placeholder="0.00" required /></div></label>
                  <label className="amount-field"><span>Description <small>Optional</small></span><input name="description" maxLength={160} placeholder="What is this transfer for?" /></label>
                  <p className="balance-note">Available balance: {formatCurrency(account?.balance)}</p>
                  {transferError && <div className="form-message error">{transferError}</div>}
                  <div className="modal-actions"><button type="button" className="secondary-button" onClick={closeTransaction}>Cancel</button><button type="submit" className="primary-button">Review transfer</button></div>
                </form>
              ) : (
                <div className="modal-body transfer-confirm">
                  {transferStage === 'confirm' ? (
                    <>
                      <div className="confirmation-mark"><Send size={22} /></div>
                      <h4>Confirm this transfer</h4>
                      <p>Send <strong>{formatCurrency(transferDraft?.amount)}</strong> to <strong>{transferDraft?.recipientId}</strong>?</p>
                      {transferDraft?.description && <p className="muted-copy">{transferDraft.description}</p>}
                      <p className="balance-note">New balance: {formatCurrency(Number(account?.balance || 0) - Number(transferDraft?.amount || 0))}</p>
                      {transferError && <div className="form-message error">{transferError}</div>}
                      <div className="modal-actions"><button className="secondary-button" onClick={() => setTransferStage('input')}>Back</button><button className="primary-button" onClick={confirmTransfer} disabled={transactionLoading}>{transactionLoading ? 'Sending…' : 'Confirm transfer'}</button></div>
                    </>
                  ) : (
                    <>
                      <div className="confirmation-mark success-mark"><Check size={24} /></div>
                      <h4>Transfer complete</h4>
                      <p>{formatCurrency(transferDraft?.amount)} was sent to {transferDraft?.recipientId}.</p>
                      <button className="primary-button" onClick={closeTransaction}>Done</button>
                    </>
                  )}
                </div>
              )
            ) : (
              <>
                <div className="modal-body">
                  {transactionModal === 'withdraw' && <p className="balance-note">Available balance: {formatCurrency(account?.balance)}</p>}
                  <label className="amount-field"><span>Amount</span><div className="currency-input"><span>€</span><input type="number" min="10.01" step="0.01" value={transactionAmount} onChange={(event) => setTransactionAmount(event.target.value)} placeholder="0.00" /></div></label>
                  <div className="quick-amounts">{quickAmounts.map((amount) => <button key={amount} type="button" className="quick-chip" onClick={() => setTransactionAmount(String(amount))}>€{amount}</button>)}</div>
                  {atmMode && transactionModal === 'withdraw' && <p className="muted-copy">ATM cash withdrawals require an exact whole-euro banknote combination.</p>}
                  {transactionFeedback && <div className="form-message error">{transactionFeedback}</div>}
                </div>
                <div className="modal-actions">
                  <button className="secondary-button" onClick={closeTransaction}>Cancel</button>
                  <button className="primary-button" onClick={() => submitTransaction(transactionModal)} disabled={transactionLoading}>
                    {transactionLoading ? 'Processing…' : transactionModal === 'deposit' ? 'Deposit' : atmMode ? 'Withdraw cash' : 'Withdraw'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {selectedTransaction && (
        <div className="modal-overlay" onMouseDown={(event) => event.target === event.currentTarget && setSelectedTransaction(null)}>
          <div className="transaction-modal details-modal" role="dialog" aria-modal="true" aria-labelledby="details-title">
            <div className="modal-header"><div><p className="eyebrow primary">Ledger record</p><h3 id="details-title">{formatTransactionType(selectedTransaction.transaction_type)}</h3></div><button className="close-button" aria-label="Close details" onClick={() => setSelectedTransaction(null)}><X size={18} /></button></div>
            <div className="detail-amount">{isCredit(selectedTransaction) ? '+' : '-'}{formatCurrency(selectedTransaction.amount)}</div>
            <div className="detail-row"><span>Transaction ID</span><strong className="mono-value">{selectedTransaction.transaction_id}</strong></div>
            {selectedTransaction.transfer_id && <div className="detail-row"><span>Transfer ID</span><strong className="mono-value">{selectedTransaction.transfer_id}</strong></div>}
            <div className="detail-row"><span>Date & time</span><strong>{new Date(selectedTransaction.timestamp).toLocaleString()}</strong></div>
            <div className="detail-row"><span>Balance after</span><strong>{formatCurrency(selectedTransaction.balance_after)}</strong></div>
            <div className="detail-row"><span>Status</span><strong>{selectedTransaction.status || 'completed'}</strong></div>
            {selectedTransaction.counterparty_id && <div className="detail-row"><span>{isCredit(selectedTransaction) ? 'Sender' : 'Recipient'}</span><strong>{selectedTransaction.counterparty_name || selectedTransaction.counterparty_id} · {selectedTransaction.counterparty_id}</strong></div>}
            {selectedTransaction.description && <div className="detail-row"><span>Description</span><strong>{selectedTransaction.description}</strong></div>}
          </div>
        </div>
      )}
      {toast && <div key={toast.id} className={`toast ${toast.kind}`} role="status"><span>{toast.kind === 'success' ? <Check size={16} /> : <Activity size={16} />}</span>{toast.message}<button aria-label="Dismiss notification" onClick={() => setToast(null)}><X size={15} /></button></div>}
    </div>
  )
}

export default App
