// src/components/common/GameCard/GameCard.js
import React from "react";
import "./GameCard.css";

const GameCard = ({
  header,
  title,
  subtitle,
  mainContent,
  additionalContent,
  onClick,
  className = ""
}) => {
  return (
    <div className={`game-card ${className}`} onClick={onClick}>
      <div className="game-header">
        {header}
      </div>
      <h3 className="game-title">{title}</h3>
      {subtitle && <p className="game-subtitle">{subtitle}</p>}
      <div className="game-main-content">{mainContent}</div>
      {additionalContent && (
        <div className="game-additional-content">{additionalContent}</div>
      )}
    </div>
  );
};
export default GameCard;