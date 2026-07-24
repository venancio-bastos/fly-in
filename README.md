# fly-in







ROADMAP

1. Validar Nível:
    1.1. Ignorar comentários;
    1.2. Primeira linha ser o número de drones -> nb_drones: <number>;
    1.3. Apenas pode ter um start_hub e um end_hub:
        1.3.1 Ignorar max_drones=<number>, porque têm capacidade infinita;
    1.4. Cada hub vai ter definido desta maneira -> hub: <name> <x> <y> [metadata];
    1.5. Vai haver connnections, para ligar as hub, por isso não podem haver hífens nos nomes das mesmas:
        1.5.1. A sua representação -> connection: hub1-hub2
    1.6. As metadatas são opcionais, mas têm valor default:
        1.6.1. zone=<type> (default: normal, blocked, restricted, priority);
        1.6.2. color=<value> (default: none, any single word);
        1.6.3. Nas connections:
            1.6.3.1 max_link_capacity=<number> (default: 1) -> Máximo de drones que podem passar ao mesmo tempo;
        1.6.4. max_drones=<number> (default: 1);


2. Estrutura de dados
3. Montar a simulação
