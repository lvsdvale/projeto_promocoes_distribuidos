import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Cadastro() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isStore, setIsStore] = useState(false);
  const navigate = useNavigate();

  const handleCadastro = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      alert('As senhas não coincidem!');
      return;
    }

    try {
      const response = await api.post('/register', {
        user_email: email,
        password: password,
        is_store: isStore
      });

      alert(response.data.message || 'Cadastro realizado com sucesso!');
      navigate('/');
    } catch (error) {
      alert('Erro no cadastro: ' + (error.response?.data?.message || error.message));
    }
  };

  return (
    <div className="card">
      <h2>Criar Nova Conta</h2>
      <form onSubmit={handleCadastro}>
        <div className="form-group">
          <label>E-mail</label>
          <input 
            type="email" 
            placeholder="Digite seu e-mail" 
            value={email}
            onChange={e => setEmail(e.target.value)} 
            required 
          />
        </div>

        <div className="form-group">
          <label>Senha</label>
          <input 
            type="password" 
            placeholder="Digite sua senha" 
            value={password}
            onChange={e => setPassword(e.target.value)} 
            required 
          />
        </div>

        <div className="form-group">
          <label>Confirmar Senha</label>
          <input 
            type="password" 
            placeholder="Confirme sua senha" 
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)} 
            required 
          />
        </div>

        <div className="form-group">
          <label style={{ fontWeight: 'bold', marginBottom: '8px' }}>Tipo de Conta</label>
          <div style={{ display: 'flex', gap: '20px', marginTop: '5px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="user_type" 
                checked={!isStore} 
                onChange={() => setIsStore(false)} 
              />
              Consumidor
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
              <input 
                type="radio" 
                name="user_type" 
                checked={isStore} 
                onChange={() => setIsStore(true)} 
              />
              Loja
            </label>
          </div>
        </div>

        <button type="submit" className="btn-primary">Cadastrar</button>
      </form>

      <button className="btn-link" onClick={() => navigate('/')}>
        Já tem uma conta? Faça Login
      </button>
    </div>
  );
}