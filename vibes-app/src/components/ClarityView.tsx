import { useState, useEffect, useRef } from "react";
import "./ClarityView.css";
import { CSSTransition } from "react-transition-group";
import Countdown from "react-countdown";

export default function ClarityView({
  fortune,
  question,
  isClarityShown,
  questionAnswer,
  epochTime,
}) {
  const nodeRef = useRef(null);
  const Completionist = () => <span>And now again</span>;

  let date = new Date(0);
  date.setUTCSeconds(epochTime / 1000);

  return (
    <CSSTransition
      in={isClarityShown}
      timeout={5000}
      classNames="clarity-fade"
      nodeRef={nodeRef}
      unmountOnExit
    >
      <div ref={nodeRef}>
        <h4 className="text title is-4">{fortune}</h4>
        <h6 className="text title is-6">{question}</h6>
        <h4 className="text title is-4">{questionAnswer}</h4>
        <h5 className="is-5">
          <Countdown date={date} className="is-5">
            <Completionist />
          </Countdown>
        </h5>
      </div>
    </CSSTransition>
  );
}
