import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { user_email: email, password });
      localStorage.setItem('token', response.data.token);
      if (response.data.is_store) navigate('/loja');
      else navigate('/cliente');
    } catch (error) {
      alert('Erro no login: ' + (error.response?.data?.message || error.message));
    }
  };

  return (
    <div className="card">
      <h2>Acesso ao Sistema</h2>
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label>E-mail</label>
          <input type="email" placeholder="Digite seu e-mail" onChange={e => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Senha</label>
          <input type="password" placeholder="Digite sua senha" onChange={e => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary">Entrar</button>
      </form>
      <button className="btn-link" onClick={() => navigate('/cadastro')}>Não tem conta? Cadastre-se</button>
    </div>
  );
}