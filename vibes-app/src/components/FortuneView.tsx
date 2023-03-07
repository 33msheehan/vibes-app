import { useState, useEffect, useRef } from "react";
import { CSSTransition } from "react-transition-group";
import "./FortuneView.css";

export default function FortuneView({
  fortune,
  question = "",
  handleSubmitQuestion,
  handleInputChange,
  isFortuneShown,
}) {
  const nodeRef = useRef(null);
  return (
    <CSSTransition
      in={isFortuneShown}
      timeout={8000}
      classNames="fortune-fade"
      nodeRef={nodeRef}
      unmountOnExit
    >
      <div ref={nodeRef}>
        <h3 className="text title is-3">{fortune}</h3>
        <form onSubmit={handleSubmitQuestion}>
          <input
            className="input-clarity input question-bar is-rounded is-light is-large is-outlined"
            type="text"
            placeholder="Devine Further Clarity"
            value={question}
            onChange={handleInputChange}
          />
        </form>
      </div>
    </CSSTransition>
  );
}
