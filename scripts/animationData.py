from scripts.custom_data_types import AnimationDataCollection, AnimationData

TIME_FOR_ONE_LOGICAL_STEP = 0.01666666666666666

PLAYER_ANIMATION_DATA = [
    AnimationData('idle',4,6,False,True),
    AnimationData('crouch',1,4,True,False),
    AnimationData('jump_up',1,5,True,False),
    AnimationData('jump_down',4,5,True,False),
    AnimationData('land',6,2,False,False),
    AnimationData('run',6,4,False,True),
    AnimationData('slide',1,5,True,False),
    AnimationData('wall_slide',1,4,True,False),
    AnimationData('sprint',6,3,False,True)
]

PARTICLE_ANIMATION_DATA = {
    'jump': AnimationData('jump',9,2,True,False),
    'land': AnimationData('land',4,2,True,False),
    'big_land': AnimationData('big_land',11,2,True,False),
    'ak47_smoke':AnimationData('ak47_smoke',3,3,False,False)
}

PARTICLE_ANIMATION_PIVOTS = {
    'jump':(0,0),
    'land':(0,0),
    'big_land': (0,0),
    'ak47_smoke': (2,4)
}

PlayerAnimationDataCollection = AnimationDataCollection(PLAYER_ANIMATION_DATA)  


