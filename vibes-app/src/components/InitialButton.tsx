import { useState, useEffect, useRef } from "react";
import { CSSTransition } from "react-transition-group";
import "./InitalButton.css";

export default function InitialButton({ isButtonShown, handleButtonPress }) {
  const nodeRef = useRef(null);

  return (
    <CSSTransition
      in={isButtonShown}
      timeout={1000}
      classNames="fade"
      nodeRef={nodeRef}
      unmountOnExit
      appear
    >
      <button
        className="button is-light is-large is-outlined"
        ref={nodeRef}
        onClick={handleButtonPress}
      >
        Discover External Truth
      </button>
    </CSSTransition>
  );
}
