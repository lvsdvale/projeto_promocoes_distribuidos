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
      
      // Redireciona dependendo se é loja ou cliente normal
      if (response.data.is_store) {
        navigate('/loja');
      } else {
        navigate('/cliente');
      }
    } catch (error) {
      alert('Erro no login: ' + error.response?.data?.message);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>
      <input type="email" placeholder="E-mail" onChange={e => setEmail(e.target.value)} required />
      <input type="password" placeholder="Senha" onChange={e => setPassword(e.target.value)} required />
      <button type="submit">Entrar</button>
      <button type="button" onClick={() => navigate('/cadastro')}>Ir para Cadastro</button>
    </form>
  );
}