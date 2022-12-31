#
# Copyright (c) 2012-2017 The ANTLR Project. All rights reserved.
# Use of this file is governed by the BSD 3-clause license that
# can be found in the LICENSE.txt file in the project root.
#

from antlr4 import TokenStream
from antlr4.atn.ATNConfigSet import ATNConfigSet

#
# This is the base class for gathering detailed information about prediction
# events which occur during parsing.
#
# Note that we could record the parser call stack at the time this event
# occurred but in the presence of left recursive rules, the stack is kind of
# meaningless. It's better to look at the individual configurations for their
# individual stacks. Of course that is a {@link PredictionContext} object
# not a parse tree node and so it does not have information about the extent
# (start...stop) of the various subtrees. Examining the stack tops of all
# configurations provide the return states for the rule invocations.
# From there you can get the enclosing rule.
#
# @since 4.3
#

class DecisionEventInfo(object):
    __slots__ = (
        'decision',
        'configs',
        'input',
        'startIndex',
        'stopIndex',
        'fullCtx'
    )
    #
    # The invoked decision number which this event is related to.
    #
    # @see ATN#decisionToState
    #
    # decision

    #
    # The configuration set containing additional information relevant to the
    # prediction state when the current event occurred, or {@code null} if no
    # additional information is relevant or available.
    #
    # configs

    #
    # The input token stream which is being parsed.
    #
    # input

    #
    # The token index in the input stream at which the current prediction was
    # originally invoked.
    #
    # startIndex

    #
    # The token index in the input stream at which the current event occurred.
    #
    # stopIndex

    #
    # {@code true} if the current event occurred during LL prediction
    # otherwise, {@code false} if the input occurred during SLL prediction.
    #
    # fullCtx

    def __init__(self, decision:int, configs:ATNConfigSet, input:TokenStream, startIndex:int, stopIndex:int, fullCtx:bool):
        self.decision = decision
        self.fullCtx = fullCtx
        self.stopIndex = stopIndex
        self.input = input
        self.startIndex = startIndex
        self.configs = configs
