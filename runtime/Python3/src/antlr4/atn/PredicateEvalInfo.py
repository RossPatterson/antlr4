#
#  Copyright (c) 2012-2017 The ANTLR Project. All rights reserved.
#  Use of self file is governed by the BSD 3-clause license that
#  can be found in the LICENSE.txt file in the project root.
#

from antlr4 import TokenStream
from antlr4.atn.ATNConfigSet import ATNConfigSet
from antlr4.atn.DecisionEventInfo import DecisionEventInfo
from antlr4.atn.SemanticContext import SemanticContext
#
#  self class represents profiling event information for semantic predicate
#  evaluations which occur during prediction.
#
#  @see ParserATNSimulator#evalSemanticContext
#
#  @since 4.3
#
class PredicateEvalInfo(DecisionEventInfo)
	__slots__ = (semctx, predictedAlt, evalResult)

	#
	#  The semantic context which was evaluated.
	#
	# SemanticContext semctx
	#
	#  The alternative number for the decision which is guarded by the semantic
	#  context {@link #semctx}. Note that other ATN
	#  configurations may predict the same alternative which are guarded by
	#  other semantic contexts and/or {@link SemanticContext#NONE}.
	#
	# int predictedAlt
	#
	#  The result of evaluating the semantic context {@link #semctx}.
	#
	# boolean evalResult

	#
	#  Constructs a new instance of the {@link PredicateEvalInfo} class with the
	#  specified detailed predicate evaluation information.
	#
	#  @param decision The decision number
	#  @param input The input token stream
	#  @param startIndex The start index for the current prediction
	#  @param stopIndex The index at which the predicate evaluation was
	#  triggered. Note that the input stream may be reset to other positions for
	#  the actual evaluation of individual predicates.
	#  @param semctx The semantic context which was evaluated
	#  @param evalResult The results of evaluating the semantic context
	#  @param predictedAlt The alternative number for the decision which is
	#  guarded by the semantic context {@code semctx}. See {@link #predictedAlt}
	#  for more information.
	#  @param fullCtx {@code true} if the semantic context was
	#  evaluated during LL prediction; otherwise, {@code false} if the semantic
	#  context was evaluated during SLL prediction
	#
	#  @see ParserATNSimulator#evalSemanticContext(SemanticContext, ParserRuleContext, int, boolean)
	#  @see SemanticContext#eval(Recognizer, RuleContext)
	#
    def __init__(self, decision:int, input:TokenStream, startIndex:int, stopIndex:int, semctx:SemanticContext, evalResult:bool, predictedAlt:int, fullCtx:bool):
        super().__init__(decision, ATNConfigSet(), input, startIndex, stopIndex, fullCtx)
		self.semctx = semctx;
		self.evalResult = evalResult;
		self.predictedAlt = predictedAlt;
