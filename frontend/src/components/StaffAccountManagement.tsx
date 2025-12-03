import React, { useState } from 'react';

interface CreateUserForm {
  email: string;
  password: string;
  role: 'fulfillment_partner' | 'influencer';
}

interface LoginForm {
  email: string;
  password: string;
}

interface User {
  user_id: string;
  email: string;
  role: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

const StaffAccountManagement: React.FC = () => {
  // 사용자 생성 폼
  const [createForm, setCreateForm] = useState<CreateUserForm>({
    email: '',
    password: '',
    role: 'fulfillment_partner',
  });
  const [createdUsers, setCreatedUsers] = useState<User[]>([]);
  const [createLoading, setCreateLoading] = useState(false);
  const [createMessage, setCreateMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 로그인 폼
  const [loginForm, setLoginForm] = useState<LoginForm>({
    email: '',
    password: '',
  });
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginMessage, setLoginMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loginToken, setLoginToken] = useState<LoginResponse | null>(null);

  const API_BASE_URL = 'http://localhost:8000';

  // 사용자 생성 핸들러
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '사용자 생성 실패');
      }

      const user = await response.json();
      setCreatedUsers([...createdUsers, user]);
      setCreateMessage({
        type: 'success',
        text: `✅ ${user.email} (${user.role}) 생성 완료!`,
      });

      // 폼 초기화
      setCreateForm({
        email: '',
        password: '',
        role: 'fulfillment_partner',
      });
    } catch (error) {
      setCreateMessage({
        type: 'error',
        text: `❌ ${error instanceof Error ? error.message : '오류 발생'}`,
      });
    } finally {
      setCreateLoading(false);
    }
  };

  // 로그인 핸들러
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/fulfillment-partner/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '로그인 실패');
      }

      const data = await response.json();
      setLoginToken(data);
      setLoginMessage({
        type: 'success',
        text: `✅ 로그인 성공!`,
      });
    } catch (error) {
      setLoginMessage({
        type: 'error',
        text: `❌ ${error instanceof Error ? error.message : '로그인 실패'}`,
      });
    } finally {
      setLoginLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">👥 동료 계정 관리</h1>
        <p className="text-gray-600 mb-8">배송담당자 및 인플루언서 계정 생성</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 사용자 생성 섹션 */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">👤 계정 생성</h2>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <input
                  type="email"
                  value={createForm.email}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, email: e.target.value })
                  }
                  placeholder="user@example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호
                </label>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, password: e.target.value })
                  }
                  placeholder="비밀번호"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  역할
                </label>
                <select
                  value={createForm.role}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      role: e.target.value as 'fulfillment_partner' | 'influencer',
                    })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="fulfillment_partner">배송담당자 (fulfillment_partner)</option>
                  <option value="influencer">인플루언서 (influencer)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={createLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition"
              >
                {createLoading ? '생성 중...' : '계정 생성'}
              </button>
            </form>

            {/* 메시지 */}
            {createMessage && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  createMessage.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {createMessage.text}
              </div>
            )}

            {/* 생성된 사용자 목록 */}
            {createdUsers.length > 0 && (
              <div className="mt-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4">✅ 생성된 계정</h3>
                <div className="space-y-2">
                  {createdUsers.map((user) => (
                    <div
                      key={user.user_id}
                      className="p-3 bg-gray-50 border border-gray-200 rounded-lg flex justify-between items-center"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{user.email}</p>
                        <p className="text-sm text-gray-600">{user.role}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(user.user_id)}
                        className="text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded"
                        title="ID 복사"
                      >
                        복사
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 로그인 테스트 섹션 */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🔑 로그인 테스트</h2>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(e) =>
                    setLoginForm({ ...loginForm, email: e.target.value })
                  }
                  placeholder="user@example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호
                </label>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(e) =>
                    setLoginForm({ ...loginForm, password: e.target.value })
                  }
                  placeholder="비밀번호"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition"
              >
                {loginLoading ? '로그인 중...' : '로그인'}
              </button>
            </form>

            {/* 메시지 */}
            {loginMessage && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  loginMessage.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {loginMessage.text}
              </div>
            )}

            {/* 토큰 정보 */}
            {loginToken && (
              <div className="mt-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4">🎫 토큰 정보</h3>
                <div className="space-y-3">
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Access Token:</p>
                    <p className="text-xs font-mono break-all text-gray-900 truncate">
                      {loginToken.access_token.substring(0, 50)}...
                    </p>
                    <button
                      onClick={() => copyToClipboard(loginToken.access_token)}
                      className="mt-2 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-2 py-1 rounded"
                    >
                      토큰 복사
                    </button>
                  </div>
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <p className="text-xs text-gray-600">Token Type:</p>
                    <p className="text-sm font-medium text-gray-900">{loginToken.token_type}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 더미 계정 정보 */}
            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-bold text-blue-900 mb-3">📝 테스트 계정</h4>
              <div className="space-y-2 text-sm text-blue-800">
                <p>
                  <strong>NCR:</strong> ncr@fulfillment.com / Partner@NCR123
                </p>
                <p>
                  <strong>Luzon:</strong> luzon@fulfillment.com / Partner@Luzon123
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StaffAccountManagement;
