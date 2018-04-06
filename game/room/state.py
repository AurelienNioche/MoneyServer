from game.models import User

# Global states
welcome = "welcome"
survey = "survey"
tutorial = "tutorial"
game = "game"
end = "end"


def get_progress_for_current_state(rm):

    if rm.state == welcome:

        # Count users assigned to the room
        n_user = User.objects.filter(room_id=rm.id).count()

        return round(n_user / rm.n_user * 100)

    elif rm.state == survey:

        # Get player with age and gender assigned
        n_user = User.objects.filter(room_id=rm.id).exclude(age=None, gender=None).count()

        return round(n_user / rm.n_user * 100)

    elif rm.state == tutorial:

        n_user = User.objects.filter(room_id=rm.id, tutorial_progression=100).count()

        return round(n_user / rm.n_user * 100)

    elif rm.state == game:

        return round(rm.t / rm.ending_t * 100)


