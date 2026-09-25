import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRightLeft,
  CreditCard,
  Eye,
  EyeOff,
  Landmark,
  LogOut,
  Menu,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
  X,
} from 'lucide-react'
import { api } from './services/api'
import './App.css'

const quickAmounts = [20, 50, 100, 200]

const formatCurrency = (value) => {
  const numeric = Number.parseFloat(value ?? 0)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric)
}

const isPositive = (value) => Number.parseFloat(value ?? 0) >= 0

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function App() {
  const [user, setUser] = useState(null)
  const [account, setAccount] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [activeTab, setActiveTab] = useState('dashboard')
  const [loginForm, setLoginForm] = useState({ userId: 'user001', pin: '1234' })
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigation = useMemo(
    () => [
      { key: 'dashboard', label: 'Dashboard', icon: Wallet },
      { key: 'transactions', label: 'Transactions', icon: ArrowRightLeft },
      { key: 'account', label: 'Account', icon: CreditCard },
    ],
    [],
  )

  const loadDashboard = async () => {
    try {
      const [accountData, transactionsData] = await Promise.all([
        api.getAccount(),
        api.getTransactions(),
      ])
      setAccount(accountData)
      setTransactions(transactionsData)
    } catch (err) {
      if (err?.payload?.error?.code === 'UNAUTHORIZED' || err?.payload?.error?.code === 'SESSION_EXPIRED') {
        setUser(null)
        setAccount(null)
        setTransactions([])
      } else {
        setError(err.message || 'Unable to load account data.')
      }
    }
  }

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const session = await api.session()
        setUser({ user_id: session.user_id, name: session.name })
        await loadDashboard()
      } catch {
        setUser(null)
        setAccount(null)
        setTransactions([])
      } finally {
        setPageLoading(false)
      }
    }

    bootstrap()
  }, [])

  const handleLogin = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.login(loginForm.userId, loginForm.pin)
      const nextUser = response.user ?? response
      setUser({ user_id: nextUser.user_id || nextUser.userId, name: nextUser.name })
      setLoginForm({ userId: '', pin: '' })
      await loadDashboard()
      setRemainingAttempts(3)
      setActiveTab('dashboard')
    } catch (err) {
      const payloadError = err.payload?.error
      const detailMessage = payloadError?.message || err.message || 'Login failed.'
      setError(detailMessage)
      setRemainingAttempts(payloadError?.remaining_attempts ?? remainingAttempts)
      if (payloadError?.remaining_attempts === 0 || payloadError?.code === 'MAX_ATTEMPTS_REACHED') {
        setRemainingAttempts(0)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await api.logout()
    } finally {
      setUser(null)
      setAccount(null)
      setTransactions([])
      setTransactionModal(null)
      setTransactionAmount('')
      setTransactionFeedback('')
      setRemainingAttempts(3)
      setError('')
    }
  }

  const submitTransaction = async (type) => {
    const amount = Number.parseFloat(transactionAmount)
    if (!Number.isFinite(amount) || amount <= 0) {
      setTransactionFeedback('Enter a valid amount greater than zero.')
      return
    }

    setTransactionLoading(true)
    setTransactionFeedback('')

    try {
      const result = type === 'deposit' ? await api.deposit(amount) : await api.withdraw(amount)
      setTransactionFeedback(type === 'deposit' ? 'Deposit successful' : 'Withdrawal successful')
      setTransactionAmount('')
      await loadDashboard()
      setTimeout(() => {
        setTransactionModal(null)
        setTransactionFeedback('')
      }, 1200)
      if (result?.balance) {
        setAccount((current) => ({ ...current, balance: result.balance }))
      }
    } catch (err) {
      setTransactionFeedback(err.message || 'Transaction failed.')
    } finally {
      setTransactionLoading(false)
    }
  }

  if (pageLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="brand-block">
            <div className="brand-mark">
              <Landmark size={28} />
            </div>
            <div>
              <p className="eyebrow">MiniATM</p>
              <h1>Modern Banking</h1>
            </div>
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <label>
              <span>User ID</span>
              <input
                type="text"
                value={loginForm.userId}
                onChange={(event) => setLoginForm({ ...loginForm, userId: event.target.value })}
                placeholder="user001"
              />
            </label>

            <label>
              <span>PIN</span>
              <div className="password-wrap">
                <input
                  type={showPin ? 'text' : 'password'}
                  value={loginForm.pin}
                  onChange={(event) => setLoginForm({ ...loginForm, pin: event.target.value })}
                  placeholder="••••"
                  maxLength={4}
                />
                <button type="button" className="icon-button" onClick={() => setShowPin((current) => !current)}>
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
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  const recentTransactions = transactions.slice(0, 4)

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="brand-inline">
          <div className="brand-mark small">
            <Landmark size={22} />
          </div>
          <div>
            <p className="eyebrow">MiniATM</p>
            <h2>Banking</h2>
          </div>
        </div>

        <nav className="nav-pills">
          {navigation.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              className={activeTab === key ? 'nav-item active' : 'nav-item'}
              onClick={() => {
                setActiveTab(key)
                setMobileMenuOpen(false)
              }}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>

        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={18} />
          Logout
        </button>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="mobile-toggle-wrap">
            <button className="mobile-menu-button" onClick={() => setMobileMenuOpen((current) => !current)}>
              <Menu size={20} />
            </button>
          </div>

          <div className="user-badge">
            <div className="avatar">{user.name?.charAt(0)?.toUpperCase() || 'U'}</div>
            <div>
              <span className="label">Welcome back</span>
              <strong>{user.name}</strong>
            </div>
          </div>
        </header>

        {activeTab === 'dashboard' && (
          <section className="content-section">
            <div className="section-header">
              <div>
                <p className="eyebrow primary">{getGreeting()}, {user.name}</p>
                <h3>Here&apos;s your account overview.</h3>
              </div>
            </div>

            <div className="balance-card">
              <div className="balance-topline">
                <span>Available Balance</span>
                <button className="ghost-button" onClick={() => setShowBalance((current) => !current)}>
                  {showBalance ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              <div className="balance-value">
                {showBalance ? formatCurrency(account?.balance ?? 0) : '••••••'}
              </div>

              <div className="account-meta">
                <div>
                  <span>Account</span>
                  <strong>{account?.user_id || user.user_id}</strong>
                </div>
                <div>
                  <span>Holder</span>
                  <strong>{user.name}</strong>
                </div>
              </div>
            </div>

            <div className="quick-actions">
              <button className="action-button deposit" onClick={() => setTransactionModal('deposit')}>
                <TrendingUp size={18} />
                Deposit
              </button>
              <button className="action-button withdraw" onClick={() => setTransactionModal('withdraw')}>
                <TrendingDown size={18} />
                Withdraw
              </button>
            </div>

            <div className="transactions-panel">
              <div className="panel-header">
                <h4>Recent Transactions</h4>
                <button className="text-button" onClick={() => setActiveTab('transactions')}>View all</button>
              </div>

              <div className="transaction-list">
                {recentTransactions.length ? (
                  recentTransactions.map((transaction, index) => (
                    <div className="transaction-item" key={`${transaction.transaction_type}-${index}`}>
                      <div className="transaction-icon">
                        {transaction.transaction_type === 'deposit' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      </div>
                      <div className="transaction-copy">
                        <strong>{transaction.transaction_type === 'deposit' ? 'Deposit' : 'Withdrawal'}</strong>
                        <span>{new Date(transaction.timestamp).toLocaleString()}</span>
                      </div>
                      <div className={isPositive(transaction.amount) ? 'transaction-amount positive' : 'transaction-amount negative'}>
                        {transaction.transaction_type === 'deposit' ? '+' : '-'}
                        {formatCurrency(transaction.amount)}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">No transactions yet.</p>
                )}
              </div>
            </div>
          </section>
        )}

        {activeTab === 'transactions' && (
          <section className="content-section">
            <div className="section-header">
              <div>
                <p className="eyebrow primary">Recent activity</p>
                <h3>Transaction history</h3>
              </div>
            </div>

            <div className="transactions-panel full-width">
              <div className="transaction-list padded">
                {transactions.length ? (
                  transactions.map((transaction, index) => (
                    <div className="transaction-item" key={`${transaction.transaction_type}-${index}`}>
                      <div className="transaction-icon">
                        {transaction.transaction_type === 'deposit' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      </div>
                      <div className="transaction-copy">
                        <strong>{transaction.transaction_type === 'deposit' ? 'Deposit' : 'Withdrawal'}</strong>
                        <span>{new Date(transaction.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="transaction-meta">
                        <div className={isPositive(transaction.amount) ? 'transaction-amount positive' : 'transaction-amount negative'}>
                          {transaction.transaction_type === 'deposit' ? '+' : '-'}
                          {formatCurrency(transaction.amount)}
                        </div>
                        <small>Balance {formatCurrency(transaction.balance_after)}</small>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="empty-state">No transactions yet.</p>
                )}
              </div>
            </div>
          </section>
        )}

        {activeTab === 'account' && (
          <section className="content-section">
            <div className="section-header">
              <div>
                <p className="eyebrow primary">Account</p>
                <h3>Profile & account details</h3>
              </div>
            </div>

            <div className="account-details-card">
              <div className="detail-row">
                <span>Account holder</span>
                <strong>{user.name}</strong>
              </div>
              <div className="detail-row">
                <span>Account ID</span>
                <strong>{account?.user_id || user.user_id}</strong>
              </div>
              <div className="detail-row">
                <span>Current balance</span>
                <strong>{showBalance ? formatCurrency(account?.balance ?? 0) : '••••••'}</strong>
              </div>
              <div className="detail-row">
                <span>Security</span>
                <strong className="secure-pill"><ShieldCheck size={14} /> Protected</strong>
              </div>
            </div>
          </section>
        )}
      </main>

      {transactionModal && (
        <div className="modal-overlay" onClick={() => setTransactionModal(null)}>
          <div className="transaction-modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow primary">{transactionModal === 'deposit' ? 'Deposit' : 'Withdraw'}</p>
                <h3>{transactionModal === 'deposit' ? 'Deposit money' : 'Withdraw money'}</h3>
              </div>
              <button className="close-button" onClick={() => setTransactionModal(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              {transactionModal === 'withdraw' && (
                <p className="balance-note">Current balance: {formatCurrency(account?.balance ?? 0)}</p>
              )}

              <label className="amount-field">
                <span>Amount</span>
                <div className="currency-input">
                  <span>$</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={transactionAmount}
                    onChange={(event) => setTransactionAmount(event.target.value)}
                    placeholder="0.00"
                  />
                </div>
              </label>

              <div className="quick-amounts">
                {quickAmounts.map((amount) => (
                  <button key={amount} type="button" className="quick-chip" onClick={() => setTransactionAmount(String(amount))}>
                    ${amount}
                  </button>
                ))}
              </div>

              {transactionFeedback && <div className="form-message success">{transactionFeedback}</div>}
            </div>

            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setTransactionModal(null)}>
                Cancel
              </button>
              <button
                className="primary-button"
                onClick={() => submitTransaction(transactionModal)}
                disabled={transactionLoading}
              >
                {transactionLoading ? 'Processing...' : transactionModal === 'deposit' ? 'Deposit' : 'Withdraw'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
