import time
from typing import TYPE_CHECKING

from antlr4.atn.ATNConfigSet import ATNConfigSet
from antlr4.atn.AmbiguityInfo import AmbiguityInfo
from antlr4.atn.ContextSensitivityInfo import ContextSensitivityInfo
from antlr4.atn.DecisionInfo import DecisionInfo
from antlr4.atn.LookaheadEventInfo import LookaheadEventInfo
from antlr4.BufferedTokenStream import TokenStream
from antlr4.dfa import DFA
from antlr4.dfa.DFAState import DFAState
if TYPE_CHECKING:
    from antlr4.Parser import Parser
from antlr4.atn.ParserATNSimulator import ParserATNSimulator
from antlr4.ParserRuleContext import ParserRuleContext


class ProfilingATNSimulator(ParserATNSimulator):
    __slots__ = (
        'decisions', 'numDecisions', '_sllStopIndex', '_llStopIndex', 'currentDecision',
        'currentState', 'conflictingAltResolvedBySLL'
    )

    # At the point of LL failover, we record how SLL would resolve the conflict so that
    # we can determine whether or not a decision / input pair is context-sensitive.
    # If LL gives a different result than SLL's predicted alternative, we have a
    # context sensitivity for sure. The converse is not necessarily True, however.
    # It's possible that after conflict resolution chooses minimum alternatives,
    # SLL could get the same answer as LL. Regardless of whether or not the result indicates
    # an ambiguity, it is not treated as a context sensitivity because LL prediction
    # was not required in order to produce a correct prediction for this decision and input sequence.
    # It may in fact still be a context sensitivity but we don't know by looking at the
    # minimum alternatives for the current input.

    def __init__(self, parser:"Parser"):
        super().__init__(parser, parser._interp.atn, parser._interp.decisionToDFA, parser._interp.sharedContextCache)
        self.numDecisions = len(parser._interp.atn.decisionToState)
        self.decisions = []
        for i in range(0, self.numDecisions-1):
            self.decisions.append(DecisionInfo(i))

    def adaptivePredict(self, input:TokenStream, decision:int, outerContext:ParserRuleContext):
        try:
            self._sllStopIndex = -1
            self._llStopIndex = -1
            self.currentDecision = decision
            start = time.time_ns()
            alt = super().adaptivePredict(input, decision, outerContext)
            stop = time.time_ns()
            self.decisions[decision].timeInPrediction += (stop-start)
            self.decisions[decision].invocations+=1

            SLL_k = self._sllStopIndex - self._startIndex + 1
            self.decisions[decision].SLL_TotalLook += SLL_k
            self.decisions[decision].SLL_MinLook = SLL_k if self.decisions[decision].SLL_MinLook==0 else min(self.decisions[decision].SLL_MinLook, SLL_k)
            if SLL_k > self.decisions[decision].SLL_MaxLook:
                self.decisions[decision].SLL_MaxLook = SLL_k
                self.decisions[decision].SLL_MaxLookEvent = LookaheadEventInfo(decision, None, alt, input, self._startIndex, self._sllStopIndex, False)

            if self._llStopIndex >= 0:
                LL_k = self._llStopIndex - self._startIndex + 1
                self.decisions[decision].LL_TotalLook += LL_k
                self.decisions[decision].LL_MinLook = LL_k if self.decisions[decision].LL_MinLook==0 else min(self.decisions[decision].LL_MinLook, LL_k)
                if LL_k > self.decisions[decision].LL_MaxLook:
                    self.decisions[decision].LL_MaxLook = LL_k
                    self.decisions[decision].LL_MaxLookEvent = LookaheadEventInfo(decision, None, alt, input, self._startIndex, self._llStopIndex, True)

            return alt
        finally:
            self.currentDecision = -1

    def getExistingTargetState(self, previousD:DFAState, t:int):
        # this method is called after each time the input position advances
        # during SLL prediction
        self._sllStopIndex = self._input.index

        existingTargetState = super().getExistingTargetState(previousD, t)
        if existingTargetState is not None:
            self.decisions[self.currentDecision].SLL_DFATransitions+=1 # count only if we transition over a DFA state
            if existingTargetState is self.ERROR:
                self.decisions[self.currentDecision].errors.add(
                    ErrorInfo(self.currentDecision, previousD.configs, self._input, self._startIndex, self._sllStopIndex, False)
                )

        self.currentState = existingTargetState
        return existingTargetState

    def computeTargetState(self, dfa:DFA, previousD:DFAState, t:int):
        state = super().computeTargetState(dfa, previousD, t)
        self.currentState = state
        return state

    def computeReachSet(self, closure:ATNConfigSet, t:int, fullCtx:bool):
        if fullCtx:
            # this method is called after each time the input position advances
            # during full context prediction
            self._llStopIndex = self._input.index

        reachConfigs = super().computeReachSet(closure, t, fullCtx)
        if fullCtx:
            self.decisions[self.currentDecision].LL_ATNTransitions+=1 # count computation even if error
            if reachConfigs is not None:
                pass
            else: # no reach on current lookahead symbol. ERROR.
                # TODO: does not handle delayed errors per getSynValidOrSemInvalidAltThatFinishedDecisionEntryRule()
                self.decisions[self.currentDecision].errors.add(
                    ErrorInfo(self.currentDecision, closure, self._input, self._startIndex, self._llStopIndex, True)
                )
        else:
            self.decisions[self.currentDecision].SLL_ATNTransitions+=1
            if reachConfigs is not None:
                pass
            else: # no reach on current lookahead symbol. ERROR.
                self.decisions[self.currentDecision].errors.add(
                    ErrorInfo(self.currentDecision, closure, self._input, self._startIndex, self._sllStopIndex, False)
                )
        return reachConfigs

    def evalSemanticContext(self, predPredictions:list, outerContext:ParserRuleContext, complete:bool):
        result = super().evalSemanticContext(pred, parserCallStack, alt, fullCtx)
        if pred is not SemanticContext.PrecedencePredicate:
            fullContext = self._llStopIndex >= 0
            stopIndex = self._llStopIndex if fullContext else self._sllStopIndex
            self.decisions[self.currentDecision].predicateEvals.add(
                PredicateEvalInfo(self.currentDecision, self._input, self._startIndex, stopIndex, pred, result, alt, fullCtx)
            )
        return result

    def reportAttemptingFullContext(self, dfa:DFA, conflictingAlts:set, configs:ATNConfigSet, startIndex:int, stopIndex:int):
        if conflictingAlts is not None:
            self.conflictingAltResolvedBySLL = list(conflictingAlts)[0]
        else:
            self.conflictingAltResolvedBySLL = list(configs)[0]
        self.decisions[self.currentDecision].LL_Fallback+=1
        super().reportAttemptingFullContext(dfa, conflictingAlts, configs, startIndex, stopIndex)

    def reportContextSensitivity(self, dfa:DFA, prediction:int, configs:ATNConfigSet, startIndex:int, stopIndex:int):
        if prediction != self.conflictingAltResolvedBySLL:
            self.decisions[self.currentDecision].contextSensitivities.append(ContextSensitivityInfo(self.currentDecision, configs, self._input, startIndex, stopIndex))
        super().reportContextSensitivity(dfa, prediction, configs, startIndex, stopIndex);

    def reportAmbiguity(self, dfa:DFA, D:DFAState, startIndex:int, stopIndex:int,
                                   exact:bool, ambigAlts:set, configs:ATNConfigSet ):
        if ambigAlts is not None:
            prediction = list(ambigAlts)[0]
        else:
            prediction = list(configs)[0]
        if configs.fullCtx and prediction != self.conflictingAltResolvedBySLL:
            # Even though this is an ambiguity we are reporting, we can
            # still detect some context sensitivities.  Both SLL and LL
            # are showing a conflict, hence an ambiguity, but if they resolve
            # to different minimum alternatives we have also identified a
            # context sensitivity.
            self.decisions[self.currentDecision].contextSensitivities.append(ContextSensitivityInfo(self.currentDecision, configs, self._input, startIndex, stopIndex))
        self.decisions[self.currentDecision].ambiguities.append(
            AmbiguityInfo(self.currentDecision, configs, ambigAlts,
                              self._input, startIndex, stopIndex, configs.fullCtx)
        )
        super().reportAmbiguity(dfa, D, startIndex, stopIndex, exact, ambigAlts, configs)
