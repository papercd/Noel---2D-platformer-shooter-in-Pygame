from scripts.custom_data_types import AnimationDataCollection, AnimationData


PLAYER_ANIMATION_DATA = [
    AnimationData('idle',4,6,False,True),
    AnimationData('crouch',1,4,True,False),
    AnimationData('jump_up',1,5,True,False),
    AnimationData('jump_down',4,5,True,False),
    AnimationData('land',6,2,False,False),
    AnimationData('run',6,4,False,True),
    AnimationData('slide',1,5,True,False),
    AnimationData('wall_slide',1,4,True,False),
]

PARTICLE_ANIMATION_DATA = {
    'jump': AnimationData('jump',2,5,True,False),
    'land': AnimationData('land',3,5,True,False),
    'big_land': AnimationData('big_land',2,5,True,False),
}


PlayerAnimationDataCollection = AnimationDataCollection(PLAYER_ANIMATION_DATA)  


