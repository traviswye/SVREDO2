import React from 'react';
import '../css/GameFilterButtons.css';

const GameFilterButtons = ({ games, activeGame, onGameFilter }) => {
    if (!games || games.length === 0) {
        return null;
    }

    return (
        <div className="game-filters">
            <button
                onClick={() => onGameFilter(null)}
                className={activeGame === null ? 'active' : ''}
            >
                All Games
            </button>
            {games.map(game => (
                <button
                    key={game}
                    onClick={() => onGameFilter(game)}
                    className={activeGame === game ? 'active' : ''}
                >
                    {game}
                </button>
            ))}
        </div>
    );
};

export default GameFilterButtons;