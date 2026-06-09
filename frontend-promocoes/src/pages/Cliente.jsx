import { useEffect, useState } from 'react';
import api from '../api';

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

export default function Cliente() {
  const [promocoes, setPromocoes] = useState([]);
  const [categoria, setCategoria] = useState('');
  const [notificacoes, setNotificacoes] = useState([]);
  
  // 🌟 Lendo os interesses direto da memória do navegador (Plano B) 🌟
  const [meusInteresses, setMeusInteresses] = useState(() => {
    const salvas = localStorage.getItem('minhas_categorias');
    return salvas ? JSON.parse(salvas) : [];
  });

  const token = localStorage.getItem('token');
  const decoded = parseJwt(token);
  const userEmail = decoded ? decoded.user_email : '';

  // 🌟 Função de carregamento que usa a memória local 🌟
  const carregarTudo = async (categoriasAtuais) => {
    const currentToken = localStorage.getItem('token');
    const config = { headers: { Authorization: `Bearer ${currentToken}` } };

    try {
      const resPromo = await api.get('/promotion/list', config);
      const todasAsPromos = resPromo.data.promotions || [];

      // Filtra usando a lista que passamos para a função
      const promosFiltradas = todasAsPromos.filter(p => {
        const catPromo = p.categoria ? p.categoria.toLowerCase().trim() : "";
        return categoriasAtuais.includes(catPromo);
      });
      
      setPromocoes(promosFiltradas);
    } catch (error) {
      console.error("Erro ao carregar as promoções:", error);
    }
  };

  useEffect(() => {
    carregarTudo(meusInteresses);

    const eventSource = new EventSource(`http://localhost:5000/promotions/stream?channel=${userEmail}`);
    const globalEventSource = new EventSource('http://localhost:5000/promotions/stream');

    globalEventSource.addEventListener('nova_promocao_geral', () => {
      const catAtualizadas = JSON.parse(localStorage.getItem('minhas_categorias') || '[]');
      carregarTudo(catAtualizadas); 
    });

    globalEventSource.addEventListener('hotdeal_broadcast', (event) => {
      const data = JSON.parse(event.data);
      setNotificacoes(prev => [`🔥 HOT DEAL: O produto ID ${data.id} atingiu o limite de votos!`, ...prev]);
      const catAtualizadas = JSON.parse(localStorage.getItem('minhas_categorias') || '[]');
      carregarTudo(catAtualizadas);
    });

    eventSource.addEventListener('categoria_update', (event) => {
      const data = JSON.parse(event.data);
      setNotificacoes(prev => [`🔔 Nova promo de ${data.categoria.toUpperCase()}: ${data.nome}`, ...prev]);
      const catAtualizadas = JSON.parse(localStorage.getItem('minhas_categorias') || '[]');
      carregarTudo(catAtualizadas);
    });

    return () => {
      eventSource.close();
      globalEventSource.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail]);

  const inscreverCategoria = async (e) => {
    e.preventDefault();
    if (!categoria) return;
    
    try {
      const catLimpa = categoria.toLowerCase().trim();
      
      // Manda pro backend para os eventos SSE funcionarem
      await api.post('/promotion/subscribe', { category: catLimpa });
      
      // 🌟 Salva no navegador para o React lembrar do filtro 🌟
      const novasCategorias = [...new Set([...meusInteresses, catLimpa])];
      setMeusInteresses(novasCategorias);
      localStorage.setItem('minhas_categorias', JSON.stringify(novasCategorias));

      alert(`Você se inscreveu com sucesso na categoria: ${catLimpa}`);
      setCategoria('');
      
      // Já recarrega a vitrine na mesma hora com a nova categoria
      carregarTudo(novasCategorias);
    } catch (error) {
      alert('Erro ao se inscrever: ' + (error.response?.data?.message || error.message));
    }
  };

  const votar = async (id, voto) => {
    try {
      await api.post('/promotion/vote', { promotion_id: id, vote: voto });
      alert('Voto computado!');
      carregarTudo(meusInteresses);
    } catch (error) {
      alert('Erro ao votar: ' + (error.response?.data?.message || error.message));
    }
  };

  // Função extra para limpar as categorias caso você queira resetar
  const limparCategorias = () => {
    setMeusInteresses([]);
    localStorage.removeItem('minhas_categorias');
    carregarTudo([]);
  }

  return (
    <div style={{ background: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', width: '100%', maxWidth: '600px', margin: '20px auto', fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ textAlign: 'center', color: '#0056b3', marginTop: 0, borderBottom: '2px solid #0056b3', paddingBottom: '10px' }}>
        Painel do Consumidor
      </h2>

      <div style={{ fontSize: '13px', color: '#555', background: '#f5f5f5', padding: '8px', borderRadius: '4px', marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div><strong>Suas Categorias:</strong> {meusInteresses.length === 0 ? "Nenhuma categoria seguida" : meusInteresses.join(', ')}</div>
        {meusInteresses.length > 0 && (
          <button onClick={limparCategorias} style={{ padding: '4px 8px', fontSize: '11px', cursor: 'pointer', background: '#ffeded', color: '#cc0000', border: '1px solid #cc0000', borderRadius: '4px' }}>Limpar</button>
        )}
      </div>
      
      <div style={{ marginBottom: '25px', marginTop: '10px' }}>
        <form onSubmit={inscreverCategoria}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
            Acompanhar Nova Categoria:
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input 
              placeholder="Ex: computador, jogos, livros..." 
              value={categoria}
              onChange={e => setCategoria(e.target.value)}
              required
              style={{ flex: 1, padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
            <button type="submit" style={{ padding: '10px 20px', backgroundColor: '#0056b3', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
              Seguir
            </button>
          </div>
        </form>
      </div>

      <div style={{ background: '#eef6ff', padding: '15px', borderRadius: '6px', marginBottom: '25px', borderLeft: '5px solid #0056b3' }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#0056b3', display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span>🔔</span> Feed de Notificações ao Vivo (SSE)
        </h4>
        {notificacoes.length === 0 ? (
          <p style={{ margin: 0, fontSize: '13px', color: '#666', fontStyle: 'italic' }}>
            Aguardando novas promoções ou Hot Deals de seu interesse...
          </p>
        ) : (
          <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#333' }}>
              {notificacoes.map((n, i) => (
                <li key={i} style={{ marginBottom: '6px', lineHeight: '1.4' }}>{n}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div>
        <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '16px' }}>🏷️ Suas Promoções de Interesse</h4>
        {promocoes.length === 0 ? (
          <p style={{ color: '#777', fontSize: '14px', fontStyle: 'italic', background: '#fff3cd', padding: '10px', borderRadius: '4px', border: '1px solid #ffeeba' }}>
            Nenhuma promoção correspondente aos seus interesses está ativa no momento.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {promocoes.map(p => (
              <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', border: '1px solid #ddd', borderRadius: '6px', background: '#fafafa' }}>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '15px', color: '#222' }}>{p.nome}</div>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    Categoria: <span style={{ background: '#e0e0e0', padding: '2px 6px', borderRadius: '4px', fontWeight: '500' }}>{p.categoria}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => votar(p.id, 1)} style={{ cursor: 'pointer', padding: '6px 12px', background: '#e6f4ea', border: '1px solid #34a853', borderRadius: '4px', color: '#137333', fontWeight: 'bold' }}>👍 Gostei</button>
                  <button onClick={() => votar(p.id, -1)} style={{ cursor: 'pointer', padding: '6px 12px', background: '#fce8e6', border: '1px solid #ea4335', borderRadius: '4px', color: '#c5221f', fontWeight: 'bold' }}>👎 Ruim</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}