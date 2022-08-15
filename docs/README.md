# Bodhi: Agent Based Modelling Library


After wasting my time for the last 6 hours trying to figure out some kind of design, I'm realizing that I didn't really go in with a plan. Therefore, I'm wasting with writing software. I'm going to spend the next two to three hours writing a design document that explicitly describes both the rationale and design of the library in question.


## Overview

Bodhi is supposed to be an easier way to have scalable agent-based modeling software. The purpose is to allow users to compose complex highly scalable environments like they would a PyTorch, Mesa, and Gym program, yet be able to instantly scale and provide logs to an outside system. 

Normally, one has to use an entity component system to generate scalable agent-based modeling software. While it does solve a lot of inherent problems with coupling parts of code to each other, it feels less intuitive to develop software than writing simple OOP style software. The goal is to allow the user to define simple objects (behaviors, states, context, resources) in a hierarchical way, then run desired logic like a OpenAI Gym.

<!-- , I want to be able to simply declare objects within one  -->

### Intent

Use metaprogramming to make scalable environments while having imperative programming.

### Problem 

When creating an OpenAI gym or Mesa application clashes with the scalable methods of ECS systems. The best way to do this is to 

The `Env` is usually declared as a `world` object. Logic to push the environment forward is usually done using the `step` function. On that step, a scheduler runs through and executes the step command on each agent. The scheduler returns each agent, the state is updated each agent's step function. Hash.ai, a well-designed agent-based modeling system (I'll likely use at some point), has states and behaviors defined separately from each other. This is a decoupled approach that allows for scalable environments. There's an issue with this approach. **Cohesion and strategic coupling is missing, dynamically controlling behavior on agents and environments are not supported, and tight integration with python's many libraries is not immediately available without jumping through extra steps**. 

This can be problematic when we want to have an entity that has private methods. If we want to create systems and entities without using the agent interface directly. The setup also makes it hard to use type inference on objects. This could be something we would want for safety. I want to be able to have the scalability and native logging as hash.ai does, while still maintaining high python compatibility.


## Requirements

1. High-speed
2. Compatibility with an online system.
3. Compatibility with OpenAI gym.
4. Python definition of agents, support classes, and behaviors (Python ecosystem bro)
5. Instant logging and reporting of events, messages, and states.
6. Support for structured network management.
7. Configurations defined in a single place.

### Solution Exploration

I want to start with the closest thing to Python in a game engine GDScript. It has a majority of the desired features I'd want in an agent based modeling system. 


## Solution

### Example usage of the library