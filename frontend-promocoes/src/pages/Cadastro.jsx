import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Cadastro() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isStore, setIsStore] = useState(false); // Define se é Loja ou Cliente
  const navigate = useNavigate();

  const handleCadastro = async (e) => {
    e.preventDefault();

    // Validação básica de senha no próprio front
    if (password !== confirmPassword) {
      alert('As senhas não coincidem!');
      return;
    }

    try {
      // Faz a requisição para a rota de registro do seu gateway.py
      const response = await api.post('/register', {
        user_email: email,
        password: password,
        is_store: isStore
      });

      alert(response.data.message || 'Cadastro realizado com sucesso!');
      
      // Após cadastrar, redireciona para a tela de login
      navigate('/');
    } catch (error) {
      alert('Erro no cadastro: ' + (error.response?.data?.message || error.message));
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>Criar Nova Conta</h2>
      <form onSubmit={handleCadastro}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>E-mail:</label>
          <input 
            type="email" 
            placeholder="Digite seu e-mail" 
            value={email}
            onChange={e => setEmail(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>Senha:</label>
          <input 
            type="password" 
            placeholder="Digite sua senha" 
            value={password}
            onChange={e => setPassword(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>Confirmar Senha:</label>
          <input 
            type="password" 
            placeholder="Confirme sua senha" 
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontWeight: 'bold' }}>Tipo de Conta:</label>
          <div style={{ marginTop: '5px' }}>
            <label style={{ marginRight: '15px' }}>
              <input 
                type="radio" 
                name="user_type" 
                checked={!isStore} 
                onChange={() => setIsStore(false)} 
              />
              Consumidor (Cliente)
            </label>
            <label>
              <input 
                type="radio" 
                name="user_type" 
                checked={isStore} 
                onChange={() => setIsStore(true)} 
              />
              Loja (Vendedor)
            </label>
          </div>
        </div>

        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Cadastrar
        </button>
      </form>

      <div style={{ marginTop: '15px', textAlign: 'center' }}>
        <p>Já tem uma conta? <span onClick={() => navigate('/')} style={{ color: '#007bff', cursor: 'pointer', textDecoration: 'underline' }}>Faça Login</span></p>
      </div>
    </div>
  );
}