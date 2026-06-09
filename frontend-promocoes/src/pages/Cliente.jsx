import { useEffect, useState } from 'react';
import api from '../api';

export default function Cliente() {
  const [promocoes, setPromocoes] = useState([]);
  const [categoria, setCategoria] = useState('');
  const [notificacoes, setNotificacoes] = useState([]);

  useEffect(() => {
    // Busca a lista inicial de promoções
    carregarPromocoes();

    // Configura o SSE (Server-Sent Events)
    // O flask_sse usa a rota /promotions/stream
    const eventSource = new EventSource('http://localhost:5000/promotions/stream');
    
    eventSource.addEventListener('categoria_update', (event) => {
      const data = JSON.parse(event.data);
      setNotificacoes(prev => [...prev, `Nova promo de ${data.categoria}: ${data.nome}`]);
      carregarPromocoes(); // Atualiza a lista
    });

    eventSource.addEventListener('hotdeal_broadcast', (event) => {
      const data = JSON.parse(event.data);
      setNotificacoes(prev => [...prev, `🔥 HOT DEAL ALERTA: Promo ${data.id} está bombando!`]);
    });

    return () => eventSource.close();
  }, []);

  const carregarPromocoes = async () => {
    const res = await api.get('/promotion/list');
    setPromocoes(res.data.promotions);
  };

  const inscreverCategoria = async () => {
    await api.post('/promotion/subscribe', { category: categoria });
    alert(`Inscrito na categoria: ${categoria}`);
  };

  const votar = async (id, voto) => {
    await api.post('/promotion/vote', { promotion_id: id, vote: voto });
    alert('Voto computado!');
  };

  return (
    <div>
      <h1>Área do Consumidor</h1>
      
      <div>
        <h3>Notificações (SSE em tempo real)</h3>
        <ul>{notificacoes.map((n, i) => <li key={i}>{n}</li>)}</ul>
      </div>

      <div>
        <input placeholder="Ex: smartphone" onChange={e => setCategoria(e.target.value)} />
        <button onClick={inscreverCategoria}>Seguir Categoria</button>
      </div>

      <h3>Promoções Disponíveis</h3>
      <ul>
        {promocoes.map(p => (
          <li key={p.id}>
            {p.nome} - Categoria: {p.categoria}
            <button onClick={() => votar(p.id, 1)}>👍 (+1)</button>
            <button onClick={() => votar(p.id, -1)}>👎 (-1)</button>
          </li>
        ))}
      </ul>
    </div>
  );
}