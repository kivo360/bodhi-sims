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
   1. Preferably updating the configuration online (if possible)

### Solution Exploration


#### GDScript

I want to start with GDScript. It's close to Python in style, and it works with a game engine. This is a player shooting example on GDScript.



```py
extends Sprite

signal shoot(bullet, direction, location)

var Bullet = preload("res://Bullet.tscn")

func _input(event):
    if event is InputEventMouseButton:
        if event.button_index == BUTTON_LEFT and event.pressed:
            emit_signal("shoot", Bullet, rotation, position)

func _process(delta):
    look_at(get_global_mouse_position())

```

The main scene then receives the signal from the player object (above), and sends an object on the trajectory with the given direction.

```py
func _on_Player_shoot(Bullet, direction, location):
    var b = Bullet.instance()
    add_child(b)
    b.rotation = direction
    b.position = location
    b.velocity = b.velocity.rotated(direction)

```

This showcases a couple of things:

1. Player instance that is always accessible.
2. Signals that can be called by name and propagated to any object listing to the signal.
3. Adding instances to the game/simulation.
4. Changing state of the new instance on create.

This is a beautiful way of thinking. While I could think about my problems using ECS, this would help me think about issues in terms of scenes. GDscript has many other capabilities, like `get_node(node_name)`, and `get_reference(object_name)`

#### Native Logging Capability

SQLModel uses Pydantic to work. It maps field properties of each class type a corresponding variable. For a given class with the right type, I could set variables on an attribute, and it would send the value to the database in the background on `__setattribute__`. 
```py
from svm.core.store import set_attribute

class Commons(Module, store=True):
    value1: str
    value2: int
# This would be used to set the context of a given episode
with set_context(episode='saksjkajsklas'):
    commons = Commons(value1="something", value2=value2)

```



```py
def __setattr__(self, name, value):
    config = getattr(self, '__config__', False)
    if config:
        if getattr(config, 'store', False):
            # We would set the episode here
            set_attribute(self, name, value, episode=get_episode()) # self has name and module_id. module_id would be the same as agent_id with agents.
```

Get attribute could look up the latest attributes for a given class and item. Otherwise, it would return the default attribute.

### Accessing Context

Damn dude, I just realized how important context is for an environment. I need to be able to access variables between parts of the program. Perhaps we could do something like godot and use a function like `get_context()`. 
```py
network = self.get_context('network')
```

If I need to call resources before and after a step function I could do something like:

```py
time = self.get_resource('time')
```

### 

## Solution
```py

class BondingCurve(Module):
    reserve: float
    supply: float
    kappa: float
    invariant: Optional[float] = None
    _has_init: bool = PrivateAttr(False)

    def __post_init__(self):
        self.invariant = invariant(reserve=self.reserve, supply=self.supply, power_invariant=kappa)


    def deposit(self, dai: float, current_reserve: float, current_token_supply: float):
        # Returns number of new tokens minted, and their realized price
        tokens, realized_price = mint(
            dai, current_reserve, current_token_supply, self.kappa, self.invariant
        )
        return tokens, realized_price

    def burn(
        self,
        tokens_millions: float,
        current_reserve: float,
        current_token_supply: float,
    ):
        # Returns number of DAI that will be returned (excluding exit tribute) when the user burns their tokens, with their realized price
        dai, realized_price = withdraw(
            tokens_millions,
            current_reserve,
            current_token_supply,
            self.kappa,
            cast(float, self.invariant),
        )
        return dai, realized_price

    def get_token_price(self, current_reserve: float):
        return spot_price(current_reserve, self.kappa, self.invariant)

    def get_token_supply(self, current_reserve: float):
        return supply(current_reserve, self.kappa, self.invariant)


class AgentGym(gym.Gym, Module, ABC):
    def __init__(self, *args):
        super().__init__(*args)
        
    
    def reset(self, params: dict = {}):
        bonding: BondingCurve = self.get_component('bonding_curve')
        
        bonding.history(50) # get dataframe of last 50 steps for component


    def step(self, input: Any):
        pass




```

### Example usage of the library